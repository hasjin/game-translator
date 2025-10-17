"""Unity 게임 패치 모듈 (번역 텍스트 재적용)"""
import sys
from pathlib import Path
from typing import List, Dict
import shutil
import UnityPy
from .extractor import TextEntry

try:
    import clr
    from System.Reflection import Assembly
    from System import Activator
    ASSETSTOOLS_AVAILABLE = True
except ImportError:
    ASSETSTOOLS_AVAILABLE = False


class UnityPatcher:
    """Unity 게임 패처"""

    def __init__(self, game_path: Path, backup: bool = True):
        self.game_path = Path(game_path)
        self.backup = backup

    def apply_patches(self, entries: List[TextEntry]) -> bool:
        """번역 패치 적용"""
        print(f"[Patcher] Applying {len(entries)} translations to {self.game_path}")

        if self.backup:
            self._create_backup()

        if self._is_single_bundle():
            return self._patch_bundle(entries)
        else:
            return self._patch_assets(entries)

    def _create_backup(self):
        backup_dir = self.game_path.parent / f"{self.game_path.name}_backup"
        if not backup_dir.exists():
            print(f"  Creating backup: {backup_dir}")
            shutil.copytree(self.game_path, backup_dir)
        else:
            print(f"  Backup already exists: {backup_dir}")

    def _is_single_bundle(self) -> bool:
        return (self.game_path / "data.unity3d").exists()

    def _patch_bundle(self, entries: List[TextEntry]) -> bool:
        """UnityPy로 단일 번들 패치"""
        print("  Using UnityPy for bundle patching")
        bundle_file = self.game_path / "data.unity3d"
        env = UnityPy.load(str(bundle_file))

        entry_map = {entry.context['path_id']: entry for entry in entries if entry.translated and entry.context.get('path_id')}
        patched_count = 0

        for obj in env.objects:
            if obj.path_id not in entry_map:
                continue

            entry = entry_map[obj.path_id]
            try:
                data = obj.read()

                if obj.type.name == 'GameObject' and hasattr(data, 'm_Name'):
                    data.m_Name = entry.translated
                    data.save()
                    patched_count += 1

                elif obj.type.name == 'MonoBehaviour':
                    try:
                        tree = data.read_typetree()
                        if self._patch_tree(tree, entry.text, entry.translated):
                            data.save_typetree(tree)
                            patched_count += 1
                    except:
                        pass

                elif obj.type.name == 'TextAsset' and hasattr(data, 'text'):
                    data.text = entry.translated
                    data.save()
                    patched_count += 1

            except Exception as e:
                print(f"    Error patching object {obj.path_id}: {e}")

        try:
            output_path = self.game_path / "data.unity3d.patched"
            with open(output_path, 'wb') as f:
                f.write(env.file.save())
            original = self.game_path / "data.unity3d"
            original.unlink()
            output_path.rename(original)
            print(f"  Successfully patched {patched_count} objects")
            return True
        except Exception as e:
            print(f"  Error saving patched bundle: {e}")
            return False

    def _patch_assets(self, entries: List[TextEntry]) -> bool:
        """AssetsTools.NET으로 분할 asset 패치"""
        if not ASSETSTOOLS_AVAILABLE:
            print("[ERROR] AssetsTools.NET not available")
            return False

        print("  Using AssetsTools.NET for assets patching")

        entries_by_file: Dict[str, List[TextEntry]] = {}
        for entry in entries:
            if not entry.translated:
                continue
            file_name = entry.context.get('file', '')
            if file_name not in entries_by_file:
                entries_by_file[file_name] = []
            entries_by_file[file_name].append(entry)

        dll_path = Path(__file__).parent.parent / "lib" / "AssetsTools.NET.dll"
        assembly = Assembly.LoadFrom(str(dll_path.absolute()))
        types = assembly.GetTypes()
        AssetsManager = next((t for t in types if t.Name == "AssetsManager"), None)
        manager = Activator.CreateInstance(AssetsManager)

        classdata_path = Path(__file__).parent.parent / "lib" / "classdata.tpk"
        manager.LoadClassPackage(str(classdata_path.absolute()))

        total_patched = 0

        for file_name, file_entries in entries_by_file.items():
            asset_file = self.game_path / file_name
            if not asset_file.exists():
                continue

            print(f"  Patching {file_name} ({len(file_entries)} entries)")

            try:
                inst = manager.LoadAssetsFile(str(asset_file.absolute()), False)
                unity_version = inst.file.Metadata.UnityVersion
                manager.LoadClassDatabaseFromPackage(unity_version)

                entry_map = {e.context['path_id']: e for e in file_entries}
                patched_in_file = 0

                for obj_info in inst.file.AssetInfos:
                    if obj_info.PathId not in entry_map:
                        continue

                    entry = entry_map[obj_info.PathId]
                    try:
                        base_field = manager.GetBaseField(inst, obj_info)
                        if self._patch_field(base_field, entry.text, entry.translated):
                            obj_info.SetNewData(base_field)
                            patched_in_file += 1
                    except:
                        pass

                if patched_in_file > 0:
                    output_path = str(asset_file) + ".patched"
                    with open(output_path, 'wb') as f:
                        inst.file.Write(f)
                    asset_file.unlink()
                    Path(output_path).rename(asset_file)
                    print(f"    Patched {patched_in_file} objects")
                    total_patched += patched_in_file

                manager.UnloadAll()
            except Exception as e:
                print(f"  Error patching {file_name}: {e}")

        print(f"  Successfully patched {total_patched} total objects")
        return total_patched > 0

    def _patch_tree(self, tree, original: str, translated: str, depth=0, max_depth=10) -> bool:
        """UnityPy typetree 재귀 패치"""
        if depth > max_depth:
            return False
        modified = False
        if isinstance(tree, dict):
            for k, v in tree.items():
                if isinstance(v, str) and v == original:
                    tree[k] = translated
                    modified = True
                elif isinstance(v, (dict, list)):
                    if self._patch_tree(v, original, translated, depth+1, max_depth):
                        modified = True
        elif isinstance(tree, list):
            for i, item in enumerate(tree):
                if isinstance(item, str) and item == original:
                    tree[i] = translated
                    modified = True
                elif isinstance(item, (dict, list)):
                    if self._patch_tree(item, original, translated, depth+1, max_depth):
                        modified = True
        return modified

    def _patch_field(self, field, original: str, translated: str, depth=0, max_depth=8) -> bool:
        """AssetsTools.NET field 재귀 패치"""
        if depth > max_depth or field is None or field.IsDummy:
            return False
        modified = False
        try:
            value = field.AsString
            if value == original:
                field.AsString = translated
                modified = True
        except:
            pass
        try:
            children = field.Children
            if children:
                for child in children:
                    if self._patch_field(child, original, translated, depth+1, max_depth):
                        modified = True
        except:
            pass
        return modified
