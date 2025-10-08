"""Unity 게임 텍스트 추출 (UnityPy + AssetsTools.NET)"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import UnityPy

try:
    import clr
    from System.Reflection import Assembly
    from System import Activator
    ASSETSTOOLS_AVAILABLE = True
except ImportError:
    ASSETSTOOLS_AVAILABLE = False


class TextEntry:
    """추출된 텍스트 항목"""
    def __init__(self, text: str, context: Dict[str, Any]):
        self.text = text
        self.context = context
        self.translated = None

    def to_dict(self):
        return {
            'text': self.text,
            'context': self.context,
            'translated': self.translated
        }

    @classmethod
    def from_dict(cls, data: dict):
        entry = cls(data['text'], data['context'])
        entry.translated = data.get('translated')
        return entry


class UnityTextExtractor:
    """Unity 게임 텍스트 추출기"""

    def __init__(self, game_path: Path):
        self.game_path = Path(game_path)
        self.entries: List[TextEntry] = []

    def extract(self) -> List[TextEntry]:
        """자동으로 게임 구조 감지하여 텍스트 추출"""
        if self._is_single_bundle():
            return self._extract_from_bundle()
        else:
            return self._extract_from_assets()

    def _is_single_bundle(self) -> bool:
        return (self.game_path / "data.unity3d").exists()

    def _extract_from_bundle(self) -> List[TextEntry]:
        """UnityPy로 단일 번들 파일 추출"""
        print(f"[UnityPy] Extracting from bundle: {self.game_path}")
        bundle_file = self.game_path / "data.unity3d"
        env = UnityPy.load(str(bundle_file))
        entries = []

        for obj in env.objects:
            try:
                data = obj.read()

                if obj.type.name == 'GameObject':
                    if hasattr(data, 'm_Name') and data.m_Name and len(data.m_Name) > 3:
                        entries.append(TextEntry(
                            text=data.m_Name,
                            context={'type': 'GameObject', 'path_id': obj.path_id, 'file': str(bundle_file.name)}
                        ))

                elif obj.type.name == 'MonoBehaviour':
                    try:
                        tree = data.read_typetree()
                        found_strings = self._extract_strings_from_tree(tree)
                        for text in found_strings:
                            entries.append(TextEntry(
                                text=text,
                                context={'type': 'MonoBehaviour', 'path_id': obj.path_id, 'file': str(bundle_file.name)}
                            ))
                    except:
                        pass

                elif obj.type.name == 'TextAsset':
                    if hasattr(data, 'text') and data.text and len(data.text) > 10:
                        entries.append(TextEntry(
                            text=data.text,
                            context={'type': 'TextAsset', 'path_id': obj.path_id, 'name': getattr(data, 'm_Name', ''), 'file': str(bundle_file.name)}
                        ))
            except:
                pass

        filtered = self._filter_translatable(entries)
        print(f"  Total strings: {len(entries)}, Translatable: {len(filtered)}")
        self.entries = filtered
        return filtered

    def _extract_from_assets(self) -> List[TextEntry]:
        """AssetsTools.NET으로 분할 asset 파일 추출"""
        if not ASSETSTOOLS_AVAILABLE:
            print("[ERROR] AssetsTools.NET not available")
            return []

        print(f"[AssetsTools.NET] Extracting from assets: {self.game_path}")

        dll_path = Path(__file__).parent.parent / "lib" / "AssetsTools.NET.dll"
        assembly = Assembly.LoadFrom(str(dll_path.absolute()))
        types = assembly.GetTypes()
        AssetsManager = next((t for t in types if t.Name == "AssetsManager"), None)
        manager = Activator.CreateInstance(AssetsManager)

        classdata_path = Path(__file__).parent.parent / "lib" / "classdata.tpk"
        manager.LoadClassPackage(str(classdata_path.absolute()))

        asset_files = []
        for pattern in ["*.assets", "level*", "sharedassets*", "resources.assets"]:
            asset_files.extend(list(self.game_path.glob(pattern)))

        print(f"  Found {len(asset_files)} asset files")
        entries = []

        for asset_file in asset_files[:20]:
            try:
                inst = manager.LoadAssetsFile(str(asset_file.absolute()), False)
                if inst is None:
                    continue

                unity_version = inst.file.Metadata.UnityVersion
                manager.LoadClassDatabaseFromPackage(unity_version)

                for obj_info in inst.file.AssetInfos:
                    if obj_info.TypeId in [49, 114]:
                        try:
                            base_field = manager.GetBaseField(inst, obj_info)
                            found = self._extract_strings_from_field(base_field)
                            for text in found:
                                entries.append(TextEntry(
                                    text=text,
                                    context={'type': 'MonoBehaviour' if obj_info.TypeId == 114 else 'TextAsset', 'path_id': obj_info.PathId, 'type_id': obj_info.TypeId, 'file': str(asset_file.name)}
                                ))
                        except:
                            pass

                manager.UnloadAll()
            except:
                pass

        filtered = self._filter_translatable(entries)
        print(f"  Total strings: {len(entries)}, Translatable: {len(filtered)}")
        self.entries = filtered
        return filtered

    def _extract_strings_from_tree(self, tree, depth=0, max_depth=10) -> List[str]:
        """UnityPy typetree에서 재귀적으로 문자열 추출"""
        if depth > max_depth:
            return []
        results = []
        if isinstance(tree, dict):
            for k, v in tree.items():
                if isinstance(v, str) and len(v) > 3 and any(c.isalpha() for c in v):
                    results.append(v)
                elif isinstance(v, (dict, list)):
                    results.extend(self._extract_strings_from_tree(v, depth+1, max_depth))
        elif isinstance(tree, list):
            for item in tree:
                if isinstance(item, str) and len(item) > 3 and any(c.isalpha() for c in item):
                    results.append(item)
                elif isinstance(item, (dict, list)):
                    results.extend(self._extract_strings_from_tree(item, depth+1, max_depth))
        return results

    def _extract_strings_from_field(self, field, depth=0, max_depth=8) -> List[str]:
        """AssetsTools.NET field에서 재귀적으로 문자열 추출"""
        if depth > max_depth or field is None or field.IsDummy:
            return []
        results = []
        try:
            value = field.AsString
            if value and len(value) > 3 and any(c.isalpha() for c in value):
                results.append(value)
        except:
            pass
        try:
            children = field.Children
            if children:
                for child in children:
                    results.extend(self._extract_strings_from_field(child, depth+1, max_depth))
        except:
            pass
        return results

    def _filter_translatable(self, entries: List[TextEntry]) -> List[TextEntry]:
        """번역 가능한 텍스트만 필터링"""
        filtered = []
        for entry in entries:
            text = entry.text
            if len(text) < 10:
                continue
            if not any(c.isalpha() and ord(c) < 128 for c in text):
                continue
            has_cjk = any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\uac00' <= c <= '\ud7a3' or '\u4e00' <= c <= '\u9fff' for c in text)
            if has_cjk:
                continue
            if text.startswith('Library/') or text.startswith('Assets/'):
                continue
            if text.endswith('.png') or text.endswith('.prefab') or text.endswith('.shader'):
                continue
            if len(text) > 500 and text.startswith('{'):
                continue
            filtered.append(entry)
        return filtered

    def save(self, output_path: Path):
        """추출된 텍스트 저장"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'game_path': str(self.game_path),
            'total_entries': len(self.entries),
            'entries': [entry.to_dict() for entry in self.entries]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.entries)} entries to {output_path}")

    @classmethod
    def load(cls, input_path: Path) -> 'UnityTextExtractor':
        """저장된 텍스트 로드"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        extractor = cls(Path(data['game_path']))
        extractor.entries = [TextEntry.from_dict(e) for e in data['entries']]
        return extractor
