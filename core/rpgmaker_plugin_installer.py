"""
RPG Maker 다국어 플러그인 설치 모듈

이 모듈은 RPG Maker MV/MZ 게임에 다국어 지원 플러그인을 자동으로 설치합니다.
- SimpleLanguage.js 플러그인 생성
- plugins.js 파일 수정 (플러그인 활성화)
- 한글 폰트 다운로드 및 설정 (선택사항)
"""

import json
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import shutil


class RPGMakerPluginInstaller:
    """RPG Maker 다국어 플러그인 설치 클래스"""

    PLUGIN_TEMPLATE = '''/*:
 * @plugindesc Simple multi-language support for RPG Maker MV/MZ
 * @author GameTranslator
 * @param languagesFolder
 * @text Languages Folder
 * @desc The folder containing language files (relative to game root)
 * @default data_languages
 * @param defaultLanguage
 * @text Default Language
 * @desc The default language to use (folder name in data_languages)
 * @default ko
 * @param availableLanguages
 * @text Available Languages
 * @desc Comma-separated list of available languages
 * @default original,ko
 * @help
 * Simple Language Plugin v1.0
 */
(function() {
'use strict';
var parameters = PluginManager.parameters('SimpleLanguage');
var languagesFolder = String(parameters['languagesFolder'] || 'data_languages');
var defaultLanguage = String(parameters['defaultLanguage'] || 'ko');
var availableLanguages = String(parameters['availableLanguages'] || 'original,ko').split(',');
for (var i = 0; i < availableLanguages.length; i++) { availableLanguages[i] = availableLanguages[i].trim(); }
var storedLang = null;
try { storedLang = localStorage.getItem('SimpleLanguage_currentLang'); } catch(e) {}
if (storedLang && availableLanguages.indexOf(storedLang) !== -1) { ConfigManager.language = storedLang; } else if (!ConfigManager.language) { ConfigManager.language = 'original'; }
if (ConfigManager.language) { try { localStorage.setItem('SimpleLanguage_currentLang', ConfigManager.language); } catch(e) {} }
var _ConfigManager_makeData = ConfigManager.makeData;
ConfigManager.makeData = function() { var config = _ConfigManager_makeData.call(this); config.language = this.language; return config; };
var _ConfigManager_applyData = ConfigManager.applyData;
ConfigManager.applyData = function(config) { _ConfigManager_applyData.call(this, config); this.language = config.language || 'original'; };
var filesLoadedCount = 0; var filesConvertedCount = 0;
var _XMLHttpRequest_open = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) { var lang = ConfigManager.language || 'original'; if (typeof url === 'string' && url.indexOf('.json') !== -1) { filesLoadedCount++; if (lang && lang !== 'original' && url.indexOf('data/') === 0 && url.indexOf('data_languages') === -1) { url = url.replace('data/', languagesFolder + '/' + lang + '/'); filesConvertedCount++; } } return _XMLHttpRequest_open.call(this, method, url); };
var _Window_TitleCommand_makeCommandList = Window_TitleCommand.prototype.makeCommandList;
Window_TitleCommand.prototype.makeCommandList = function() { _Window_TitleCommand_makeCommandList.call(this); if (availableLanguages.length > 1) { this.addCommand('Language / 언어', 'language'); } };
var _Window_TitleCommand_numVisibleRows = Window_TitleCommand.prototype.numVisibleRows;
Window_TitleCommand.prototype.numVisibleRows = function() { var originalRows = _Window_TitleCommand_numVisibleRows ? _Window_TitleCommand_numVisibleRows.call(this) : 3; if (availableLanguages.length > 1) { return Math.max(originalRows, this.maxItems()); } return originalRows; };
var _Window_TitleCommand_addCommand = Window_TitleCommand.prototype.addCommand;
Window_TitleCommand.prototype.addCommand = function(name, symbol, enabled, ext) { var lang = ConfigManager.language || 'original'; if (lang === 'ko' && name === '回想モード') { name = '회상 모드'; } _Window_TitleCommand_addCommand.call(this, name, symbol, enabled, ext); };
var _Window_Options_addGeneralOptions = Window_Options.prototype.addGeneralOptions;
Window_Options.prototype.addGeneralOptions = function() { _Window_Options_addGeneralOptions.call(this); if (availableLanguages.length > 1) { this.addCommand('Language', 'language'); } };
var _Window_Options_statusText = Window_Options.prototype.statusText;
Window_Options.prototype.statusText = function(index) { var symbol = this.commandSymbol(index); if (symbol === 'language') { var lang = ConfigManager.language; var names = {'original': '日本語', 'ko': '한국어', 'en': 'English', 'zh': '中文'}; return names[lang] || lang; } return _Window_Options_statusText.call(this, index); };
var _Window_Options_processOk = Window_Options.prototype.processOk;
Window_Options.prototype.processOk = function() { var index = this.index(); var symbol = this.commandSymbol(index); if (symbol === 'language') { this.changeLanguage(); } else { _Window_Options_processOk.call(this); } };
var _Window_Options_cursorRight = Window_Options.prototype.cursorRight;
Window_Options.prototype.cursorRight = function(wrap) { var index = this.index(); var symbol = this.commandSymbol(index); if (symbol === 'language') { this.changeLanguage(1); } else { _Window_Options_cursorRight.call(this, wrap); } };
var _Window_Options_cursorLeft = Window_Options.prototype.cursorLeft;
Window_Options.prototype.cursorLeft = function(wrap) { var index = this.index(); var symbol = this.commandSymbol(index); if (symbol === 'language') { this.changeLanguage(-1); } else { _Window_Options_cursorLeft.call(this, wrap); } };
Window_Options.prototype.changeLanguage = function(direction) { direction = direction || 1; var currentIndex = availableLanguages.indexOf(ConfigManager.language); var newIndex = (currentIndex + direction + availableLanguages.length) % availableLanguages.length; var newLang = availableLanguages[newIndex]; var langNames = {'original': '日本語', 'ko': '한국어', 'en': 'English', 'zh': '中文'}; var messages = {'original': '言語を' + (langNames[newLang] || newLang) + 'に変更すると\\nゲームが再起動されます。\\n\\n続けますか？', 'ko': '언어를 ' + (langNames[newLang] || newLang) + '(으)로 변경하면\\n게임이 재시작됩니다.\\n\\n계속하시겠습니까?', 'en': 'Changing language to ' + (langNames[newLang] || newLang) + ' will restart the game.\\n\\nContinue?', 'zh': '将语言更改为' + (langNames[newLang] || newLang) + '\\n将重新启动游戏。\\n\\n继续吗？'}; var message = messages[newLang] || messages['ko']; if (confirm(message)) { ConfigManager.language = newLang; ConfigManager.save(); try { localStorage.setItem('SimpleLanguage_currentLang', newLang); } catch(e) {} location.reload(); } else { ConfigManager.language = newLang; ConfigManager.save(); try { localStorage.setItem('SimpleLanguage_currentLang', newLang); } catch(e) {} this.redrawItem(this.index()); this.activate(); } };
var _Scene_Title_createCommandWindow = Scene_Title.prototype.createCommandWindow;
Scene_Title.prototype.createCommandWindow = function() { _Scene_Title_createCommandWindow.call(this); this._commandWindow.setHandler('language', this.commandLanguage.bind(this)); };
Scene_Title.prototype.commandLanguage = function() { var currentIndex = availableLanguages.indexOf(ConfigManager.language); var newIndex = (currentIndex + 1) % availableLanguages.length; var newLang = availableLanguages[newIndex]; ConfigManager.language = newLang; ConfigManager.save(); try { localStorage.setItem('SimpleLanguage_currentLang', newLang); } catch(e) {} location.reload(); };
})();'''

    # Noto Sans CJK KR 다운로드 URL
    FONT_DOWNLOAD_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"

    def __init__(self):
        """초기화"""
        pass

    def install_plugin(
        self,
        game_path: Path,
        default_language: str = "ko",
        available_languages: str = "original,ko",
        force: bool = False
    ) -> Tuple[bool, str, dict]:
        """
        다국어 플러그인 설치

        Args:
            game_path: 게임 폴더 경로
            default_language: 기본 언어 (기본값: ko)
            available_languages: 사용 가능한 언어들 (기본값: original,ko)
            force: 강제 설치 (기존 설정 덮어쓰기)

        Returns:
            (성공 여부, 메시지, 상태 정보)
        """
        try:
            game_path = Path(game_path)

            # 1. 게임 폴더 검증
            if not game_path.exists():
                return False, f"게임 폴더를 찾을 수 없습니다: {game_path}", {}

            plugins_dir = game_path / "js" / "plugins"
            if not plugins_dir.exists():
                return False, "js/plugins 폴더를 찾을 수 없습니다. RPG Maker 게임이 맞는지 확인하세요.", {}

            # 2. 기존 번역 상태 확인
            status = self.check_translation_status(game_path)

            # 3. 경고 메시지 반환 (force=False인 경우)
            if not force and status['warning_message']:
                return False, status['warning_message'], status

            # 4. data_languages 폴더 없으면 중단
            if not status['data_languages_exists']:
                return False, "❌ data_languages 폴더가 없습니다.\n먼저 '게임에 적용하기'를 실행하여 번역 파일을 생성하세요.", status

            # 5. SimpleLanguage.js 플러그인 파일 생성
            plugin_file = plugins_dir / "SimpleLanguage.js"

            # 기존 플러그인 백업 (덮어쓰기 전)
            if plugin_file.exists() and not force:
                backup_file = plugins_dir / "SimpleLanguage.js.backup"
                shutil.copy(plugin_file, backup_file)
                status['backup_created'] = str(backup_file)

            plugin_file.write_text(self.PLUGIN_TEMPLATE, encoding='utf-8')

            # 6. plugins.js 파일 수정
            plugins_js = plugins_dir.parent / "plugins.js"
            if not plugins_js.exists():
                return False, "plugins.js 파일을 찾을 수 없습니다.", status

            # plugins.js 백업
            if not force:
                backup_js = plugins_dir.parent / "plugins.js.backup"
                shutil.copy(plugins_js, backup_js)
                status['backup_js_created'] = str(backup_js)

            success, msg = self._modify_plugins_js(
                plugins_js,
                default_language,
                available_languages
            )
            if not success:
                return False, msg, status

            # 7. 성공 메시지 생성
            success_msg = f"✅ 플러그인 설치 완료!\n\n"
            success_msg += f"📁 SimpleLanguage.js 생성됨\n"
            success_msg += f"⚙️ plugins.js 수정됨\n"
            success_msg += f"🌐 기본 언어: {default_language}\n"
            success_msg += f"📋 사용 가능 언어: {available_languages}\n"

            if status.get('backup_created'):
                success_msg += f"\n💾 백업 생성: SimpleLanguage.js.backup\n"
            if status.get('backup_js_created'):
                success_msg += f"💾 백업 생성: plugins.js.backup\n"

            return True, success_msg, status

        except Exception as e:
            return False, f"플러그인 설치 중 오류 발생: {str(e)}", {}

    def _modify_plugins_js(
        self,
        plugins_js: Path,
        default_language: str,
        available_languages: str
    ) -> Tuple[bool, str]:
        """
        plugins.js 파일 수정 (플러그인 활성화)

        Args:
            plugins_js: plugins.js 파일 경로
            default_language: 기본 언어
            available_languages: 사용 가능한 언어들

        Returns:
            (성공 여부, 메시지)
        """
        try:
            # plugins.js 읽기
            content = plugins_js.read_text(encoding='utf-8')

            # $plugins 배열 파싱
            # "var $plugins =" 이후의 JSON 배열 찾기
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx == -1 or end_idx == 0:
                return False, "plugins.js 형식이 올바르지 않습니다."

            plugins_json = content[start_idx:end_idx]
            plugins = json.loads(plugins_json)

            # SimpleLanguage 플러그인이 이미 있는지 확인
            already_exists = any(p.get('name') == 'SimpleLanguage' for p in plugins)

            if already_exists:
                # 기존 플러그인 업데이트
                for p in plugins:
                    if p.get('name') == 'SimpleLanguage':
                        p['status'] = True
                        p['parameters'] = {
                            'languagesFolder': 'data_languages',
                            'defaultLanguage': default_language,
                            'availableLanguages': available_languages
                        }
                        break
            else:
                # 새 플러그인 추가 (맨 앞에)
                new_plugin = {
                    "name": "SimpleLanguage",
                    "status": True,
                    "description": "Multi-language support for the game",
                    "parameters": {
                        "languagesFolder": "data_languages",
                        "defaultLanguage": default_language,
                        "availableLanguages": available_languages
                    }
                }
                plugins.insert(0, new_plugin)

            # JSON을 문자열로 변환 (예쁘게 포맷팅하지 않고 한 줄로)
            new_plugins_json = json.dumps(plugins, ensure_ascii=False, separators=(',', ':'))

            # plugins.js 재작성
            new_content = f"// Generated by RPG Maker.\n// Do not edit this file directly.\nvar $plugins =\n{new_plugins_json};\n"
            plugins_js.write_text(new_content, encoding='utf-8')

            return True, "plugins.js 수정 완료"

        except json.JSONDecodeError as e:
            return False, f"plugins.js JSON 파싱 오류: {str(e)}"
        except Exception as e:
            return False, f"plugins.js 수정 중 오류: {str(e)}"

    def download_korean_font(
        self,
        game_path: Path,
        font_name: str = "NotoSansCJKkr-Regular.otf"
    ) -> Tuple[bool, str]:
        """
        한글 폰트 다운로드 및 설치

        Args:
            game_path: 게임 폴더 경로
            font_name: 폰트 파일명

        Returns:
            (성공 여부, 메시지)
        """
        try:
            game_path = Path(game_path)
            fonts_dir = game_path / "fonts"
            fonts_dir.mkdir(exist_ok=True)

            font_file = fonts_dir / font_name

            # 이미 폰트가 있으면 스킵
            if font_file.exists():
                return True, f"폰트가 이미 설치되어 있습니다: {font_name}"

            # 폰트 다운로드
            print(f"한글 폰트 다운로드 중: {self.FONT_DOWNLOAD_URL}")
            urllib.request.urlretrieve(self.FONT_DOWNLOAD_URL, font_file)

            return True, f"한글 폰트 다운로드 완료: {font_name}"

        except Exception as e:
            return False, f"폰트 다운로드 중 오류: {str(e)}"

    def check_translation_status(self, game_path: Path) -> dict:
        """
        번역 및 플러그인 상태 상세 확인

        Args:
            game_path: 게임 폴더 경로

        Returns:
            상태 딕셔너리:
            {
                'plugin_installed': bool,
                'plugin_enabled': bool,
                'font_installed': bool,
                'data_languages_exists': bool,
                'korean_translation_exists': bool,
                'korean_file_count': int,
                'other_languages': list,  # ['original', 'en', 'zh'] 등
                'needs_plugin': bool,      # 플러그인 설치 필요 여부
                'warning_message': str     # 경고 메시지
            }
        """
        game_path = Path(game_path)
        status = {
            'plugin_installed': False,
            'plugin_enabled': False,
            'font_installed': False,
            'data_languages_exists': False,
            'korean_translation_exists': False,
            'korean_file_count': 0,
            'other_languages': [],
            'needs_plugin': False,
            'warning_message': ''
        }

        # 플러그인 파일 확인
        plugin_file = game_path / "js" / "plugins" / "SimpleLanguage.js"
        status['plugin_installed'] = plugin_file.exists()

        # plugins.js 확인
        plugins_js = game_path / "js" / "plugins.js"
        if plugins_js.exists():
            try:
                content = plugins_js.read_text(encoding='utf-8')
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    plugins = json.loads(content[start_idx:end_idx])
                    for p in plugins:
                        if p.get('name') == 'SimpleLanguage' and p.get('status'):
                            status['plugin_enabled'] = True
                            break
            except:
                pass

        # 폰트 확인
        fonts_dir = game_path / "fonts"
        if fonts_dir.exists():
            korean_fonts = list(fonts_dir.glob("*Korean*.otf")) + \
                          list(fonts_dir.glob("*Korean*.ttf")) + \
                          list(fonts_dir.glob("Noto*KR*.otf")) + \
                          list(fonts_dir.glob("Noto*KR*.ttf"))
            status['font_installed'] = len(korean_fonts) > 0

        # data_languages 폴더 확인
        data_languages = game_path / "data_languages"
        status['data_languages_exists'] = data_languages.exists()

        if data_languages.exists():
            # 언어 폴더 목록 확인
            lang_folders = [f.name for f in data_languages.iterdir() if f.is_dir()]
            status['other_languages'] = lang_folders

            # 한국어 번역 확인
            ko_dir = data_languages / "ko"
            if ko_dir.exists():
                json_files = list(ko_dir.glob("*.json"))
                status['korean_translation_exists'] = len(json_files) > 0
                status['korean_file_count'] = len(json_files)

        # 상태별 경고 메시지 생성
        if status['data_languages_exists']:
            if status['korean_translation_exists']:
                status['warning_message'] = f"⚠️ 한국어 번역이 이미 존재합니다 ({status['korean_file_count']}개 파일)\n"

                if status['plugin_installed'] and status['plugin_enabled']:
                    status['warning_message'] += "✅ 플러그인이 이미 설치되어 있습니다.\n"
                else:
                    status['warning_message'] += "❌ 플러그인이 설치되지 않았습니다. 게임이 한국어를 로드하지 못합니다.\n"
                    status['needs_plugin'] = True

                if not status['font_installed']:
                    status['warning_message'] += "⚠️ 한글 폰트가 없습니다. 한글이 깨질 수 있습니다.\n"

            elif status['other_languages']:
                status['warning_message'] = f"ℹ️ 다국어 폴더가 존재합니다: {', '.join(status['other_languages'])}\n"
                status['warning_message'] += "❌ 한국어 번역이 없습니다.\n"
                status['needs_plugin'] = True
        else:
            status['warning_message'] = "❌ data_languages 폴더가 없습니다. 먼저 번역을 실행하세요.\n"

        return status

    def check_installation(self, game_path: Path) -> dict:
        """
        플러그인 설치 상태 확인 (간단 버전, 하위 호환성)

        Args:
            game_path: 게임 폴더 경로

        Returns:
            설치 상태 딕셔너리
        """
        status = self.check_translation_status(game_path)
        # 간단 버전은 핵심 필드만 반환
        return {
            'plugin_installed': status['plugin_installed'],
            'plugin_enabled': status['plugin_enabled'],
            'font_installed': status['font_installed'],
            'data_languages_exists': status['data_languages_exists'],
            'korean_translation_exists': status['korean_translation_exists']
        }

    def uninstall_plugin(self, game_path: Path) -> Tuple[bool, str]:
        """
        플러그인 제거

        Args:
            game_path: 게임 폴더 경로

        Returns:
            (성공 여부, 메시지)
        """
        try:
            game_path = Path(game_path)

            # 1. SimpleLanguage.js 삭제
            plugin_file = game_path / "js" / "plugins" / "SimpleLanguage.js"
            if plugin_file.exists():
                plugin_file.unlink()

            # 2. plugins.js에서 제거
            plugins_js = game_path / "js" / "plugins.js"
            if plugins_js.exists():
                content = plugins_js.read_text(encoding='utf-8')
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1

                if start_idx != -1 and end_idx != 0:
                    plugins = json.loads(content[start_idx:end_idx])
                    plugins = [p for p in plugins if p.get('name') != 'SimpleLanguage']

                    new_plugins_json = json.dumps(plugins, ensure_ascii=False, separators=(',', ':'))
                    new_content = f"// Generated by RPG Maker.\n// Do not edit this file directly.\nvar $plugins =\n{new_plugins_json};\n"
                    plugins_js.write_text(new_content, encoding='utf-8')

            return True, "플러그인 제거 완료"

        except Exception as e:
            return False, f"플러그인 제거 중 오류: {str(e)}"


# 테스트용 메인 함수
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python rpgmaker_plugin_installer.py <게임폴더경로>")
        sys.exit(1)

    game_path = Path(sys.argv[1])
    installer = RPGMakerPluginInstaller()

    # 설치 상태 확인
    print("=== 플러그인 설치 상태 ===")
    status = installer.check_installation(game_path)
    for key, value in status.items():
        print(f"{key}: {'✅' if value else '❌'}")

    # 플러그인 설치
    print("\n=== 플러그인 설치 시작 ===")
    success, msg = installer.install_plugin(game_path)
    print(msg)

    if success:
        # 폰트 다운로드
        print("\n=== 한글 폰트 다운로드 ===")
        success, msg = installer.download_korean_font(game_path)
        print(msg)
