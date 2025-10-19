"""
RPG Maker 번역 패치 내보내기 모듈

번역된 data_languages 폴더와 플러그인을 패치 형태로 내보냅니다.
사용자가 게임 폴더에 적용할 수 있는 BAT 파일과 함께 패키징합니다.
"""

import json
import shutil
from pathlib import Path
from typing import Tuple
from datetime import datetime


class PatchExporter:
    """번역 패치 내보내기 클래스"""

    def __init__(self):
        """초기화"""
        pass

    def export_patch(
        self,
        game_path: Path,
        output_path: Path,
        patch_name: str = None
    ) -> Tuple[bool, str, dict]:
        """
        번역 패치 내보내기

        Args:
            game_path: 게임 폴더 경로 (번역이 적용된)
            output_path: 패치 출력 폴더 경로
            patch_name: 패치 이름 (기본값: game_patch_YYYYMMDD)

        Returns:
            (성공 여부, 메시지, 상태 정보)
        """
        try:
            # Path 객체로 변환 및 절대 경로 확인
            game_path = Path(game_path).resolve()
            output_path = Path(output_path).resolve()

            # 경로 존재 확인
            if not game_path.exists():
                return False, f"❌ 게임 폴더를 찾을 수 없습니다: {game_path}", {}

            if not output_path.exists():
                return False, f"❌ 출력 폴더를 찾을 수 없습니다: {output_path}", {}

            # 패치 이름 설정
            if not patch_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                patch_name = f"translation_patch_{timestamp}"

            # 패치 디렉토리 생성
            patch_dir = output_path / patch_name
            print(f"[DEBUG] Creating patch directory: {patch_dir}")
            patch_dir.mkdir(parents=True, exist_ok=True)

            status = {
                'patch_dir': str(patch_dir),
                'files_copied': 0,
                'folders_created': []
            }

            # 1. data_languages 폴더 복사
            data_languages_src = game_path / "data_languages"
            if not data_languages_src.exists():
                return False, "❌ data_languages 폴더가 없습니다.\n먼저 번역을 적용하세요.", status

            data_languages_dst = patch_dir / "data_languages"
            shutil.copytree(data_languages_src, data_languages_dst, dirs_exist_ok=True)
            status['folders_created'].append('data_languages')

            # 파일 개수 카운트
            for lang_folder in data_languages_dst.iterdir():
                if lang_folder.is_dir():
                    file_count = len(list(lang_folder.glob("*.json")))
                    status['files_copied'] += file_count

            # 2. js 폴더 구조 생성
            js_dir = patch_dir / "js"
            js_plugins_dir = js_dir / "plugins"

            # 3. plugins.js 백업 및 수정본 생성
            plugins_js_src = game_path / "js" / "plugins.js"
            if plugins_js_src.exists():
                # js 폴더가 없으면 생성
                js_dir.mkdir(parents=True, exist_ok=True)
                # plugins.js를 참고용으로 복사
                plugins_js_dst = js_dir / "plugins.js.reference"
                shutil.copy2(plugins_js_src, plugins_js_dst)
                status['files_copied'] += 1

            # 4. SimpleLanguage.js 플러그인 복사 또는 생성
            plugin_src = game_path / "js" / "plugins" / "SimpleLanguage.js"
            js_plugins_dir.mkdir(parents=True, exist_ok=True)

            if plugin_src.exists():
                # 게임 폴더에 있으면 복사
                shutil.copy2(plugin_src, js_plugins_dir / "SimpleLanguage.js")
                status['folders_created'].append('js/plugins')
                status['files_copied'] += 1
            else:
                # 게임 폴더에 없으면 템플릿에서 생성
                from core.rpgmaker_plugin_installer import RPGMakerPluginInstaller
                installer = RPGMakerPluginInstaller()
                plugin_dst = js_plugins_dir / "SimpleLanguage.js"
                plugin_dst.write_text(installer.PLUGIN_TEMPLATE, encoding='utf-8')
                status['folders_created'].append('js/plugins')
                status['files_copied'] += 1
                print(f"[INFO] SimpleLanguage.js generated from template")

            # 5. BAT 파일 생성 (3개 언어)
            for lang in ['ko', 'en', 'ja']:
                bat_content = self._generate_install_bat(lang)
                bat_file = patch_dir / f"INSTALL_PATCH_{lang.upper()}.bat"
                bat_file.write_text(bat_content, encoding='utf-8')
                status['files_copied'] += 1

            # 6. README 생성 (다국어)
            readme_content = self._generate_readme()
            readme_file = patch_dir / "README.txt"
            readme_file.write_text(readme_content, encoding='utf-8')
            status['files_copied'] += 1

            # 7. plugins.js 수정 가이드 생성 (3개 언어)
            for lang in ['ko', 'en', 'ja']:
                guide_content = self._generate_plugin_guide(lang)
                guide_file = patch_dir / f"plugins_js_guide_{lang.upper()}.txt"
                guide_file.write_text(guide_content, encoding='utf-8')
                status['files_copied'] += 1

            success_msg = f"✅ 패치 내보내기 완료!\n\n"
            success_msg += f"📁 패치 위치: {patch_dir}\n"
            success_msg += f"📦 파일 개수: {status['files_copied']}개\n"
            success_msg += f"📂 폴더: {', '.join(status['folders_created'])}\n\n"
            success_msg += f"💡 사용 방법:\n"
            success_msg += f"1. 패치 폴더를 게임 폴더에 복사하거나\n"
            success_msg += f"2. INSTALL_PATCH.bat 실행 (자동 설치)\n"

            return True, success_msg, status

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return False, f"패치 내보내기 중 오류 발생: {str(e)}\n\n상세 정보:\n{error_detail}", {}

    def _generate_install_bat(self, lang: str = 'ko') -> str:
        """Windows용 자동 설치 BAT 파일 생성"""

        if lang == 'en':
            return self._generate_install_bat_en()
        elif lang == 'ja':
            return self._generate_install_bat_ja()
        else:
            return self._generate_install_bat_ko()

    def _generate_install_bat_ko(self) -> str:
        """한국어 BAT 파일"""
        return """@echo off
chcp 65001 >nul
echo ================================================
echo    RPG Maker 번역 패치 자동 설치
echo ================================================
echo.

REM 현재 폴더 확인
set "PATCH_DIR=%~dp0"
echo 패치 폴더: %PATCH_DIR%
echo.

REM 게임 폴더 입력 받기
set /p "GAME_DIR=게임 폴더 경로를 입력하세요 (예: C:\\Games\\MyGame): "

REM 입력 확인
if "%GAME_DIR%"=="" (
    echo.
    echo [ERROR] 게임 폴더 경로가 입력되지 않았습니다.
    pause
    exit /b 1
)

REM 게임 폴더 존재 확인
if not exist "%GAME_DIR%" (
    echo.
    echo [ERROR] 게임 폴더를 찾을 수 없습니다: %GAME_DIR%
    pause
    exit /b 1
)

echo.
echo ================================================
echo    설치 준비 완료
echo ================================================
echo 패치 폴더: %PATCH_DIR%
echo 게임 폴더: %GAME_DIR%
echo.
echo 다음 작업을 수행합니다:
echo 1. data_languages 폴더 복사
echo 2. SimpleLanguage.js 플러그인 설치
echo 3. plugins.js 백업 및 수정
echo.

set /p "CONFIRM=계속하시겠습니까? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo 설치가 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo ================================================
echo    패치 설치 중...
echo ================================================

REM 1. data_languages 폴더 복사
echo.
echo [1/3] data_languages 폴더 복사 중...
if exist "%PATCH_DIR%data_languages" (
    xcopy /E /I /Y "%PATCH_DIR%data_languages" "%GAME_DIR%\\data_languages" >nul
    if errorlevel 1 (
        echo [ERROR] data_languages 복사 실패
        pause
        exit /b 1
    )
    echo [OK] data_languages 복사 완료
) else (
    echo [WARNING] data_languages 폴더가 없습니다
)

REM 2. SimpleLanguage.js 플러그인 설치
echo.
echo [2/3] SimpleLanguage.js 플러그인 설치 중...
if exist "%PATCH_DIR%js\\plugins\\SimpleLanguage.js" (
    if not exist "%GAME_DIR%\\js\\plugins" mkdir "%GAME_DIR%\\js\\plugins"
    copy /Y "%PATCH_DIR%js\\plugins\\SimpleLanguage.js" "%GAME_DIR%\\js\\plugins\\SimpleLanguage.js" >nul
    if errorlevel 1 (
        echo [ERROR] 플러그인 복사 실패
        pause
        exit /b 1
    )
    echo [OK] SimpleLanguage.js 설치 완료
) else (
    echo [WARNING] SimpleLanguage.js 파일이 없습니다
)

REM 3. plugins.js 백업 및 자동 수정
echo.
echo [3/3] plugins.js 설정 중...
if exist "%GAME_DIR%\\js\\plugins.js" (
    REM 백업 생성
    if not exist "%GAME_DIR%\\js\\plugins.js.backup" (
        copy /Y "%GAME_DIR%\\js\\plugins.js" "%GAME_DIR%\\js\\plugins.js.backup" >nul
        echo [OK] plugins.js 백업 완료
    ) else (
        echo [INFO] plugins.js 백업이 이미 존재합니다
    )

    REM PowerShell로 JSON 수정
    echo [INFO] plugins.js 자동 수정 시도 중...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$file = '%GAME_DIR%\\js\\plugins.js'; ^
        $content = Get-Content $file -Raw -Encoding UTF8; ^
        if ($content -notmatch 'SimpleLanguage') { ^
            $newPlugin = '{\"\"name\"\":\"\"SimpleLanguage\"\",\"\"status\"\":true,\"\"description\"\":\"\"Multi-language support for the game\"\",\"\"parameters\"\":{\"\"languagesFolder\"\":\"\"data_languages\"\",\"\"defaultLanguage\"\":\"\"original\"\",\"\"availableLanguages\"\":\"\"original,ko\"\"}}'; ^
            $content = $content -replace '(\[)', ('$1' + [Environment]::NewLine + $newPlugin + ','); ^
            [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8); ^
            Write-Host '[OK] SimpleLanguage 플러그인 자동 추가 완료' -ForegroundColor Green; ^
        } else { ^
            Write-Host '[INFO] SimpleLanguage 플러그인이 이미 존재합니다' -ForegroundColor Yellow; ^
        }"

    if errorlevel 1 (
        echo.
        echo [WARNING] 자동 수정 실패 - 수동 수정이 필요합니다
        echo 자세한 방법은 plugins_js_guide.txt를 참고하세요.
    )
) else (
    REM plugins.js 파일이 없으면 새로 생성
    echo [WARNING] plugins.js 파일이 없습니다
    echo [INFO] 새 plugins.js 파일 생성 중...

    if not exist "%GAME_DIR%\\js" mkdir "%GAME_DIR%\\js"

    (
        echo // Generated by RPG Maker.
        echo // Do not edit this file directly.
        echo var $plugins =
        echo [
        echo {"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}}
        echo ];
    ) > "%GAME_DIR%\\js\\plugins.js"

    if exist "%GAME_DIR%\\js\\plugins.js" (
        echo [OK] plugins.js 파일 생성 완료
    ) else (
        echo [ERROR] plugins.js 파일 생성 실패
    )
)

echo.
echo ================================================
echo    패치 설치 완료!
echo ================================================
echo.
echo ✅ 설치가 완료되었습니다!
echo.
echo 다음 단계:
echo 1. 게임을 실행하세요
echo 2. 타이틀 화면에서 "Language / 언어" 메뉴 확인
echo 3. 옵션 메뉴에서 언어 변경 가능
echo.
echo 💡 참고:
echo - plugins.js가 자동으로 설정되었습니다
echo - 문제 발생 시 plugins_js_guide.txt 참고
echo.
echo ⚠️ 문제가 발생하면:
echo - js\\plugins.js.backup을 js\\plugins.js로 복사하여 복원
echo - data_languages 폴더 삭제
echo - SimpleLanguage.js 삭제
echo.

pause
"""

    def _generate_install_bat_en(self) -> str:
        """English BAT file"""
        return """@echo off
chcp 65001 >nul
echo ================================================
echo    RPG Maker Translation Patch Auto Installer
echo ================================================
echo.

REM Current folder check
set "PATCH_DIR=%~dp0"
echo Patch folder: %PATCH_DIR%
echo.

REM Get game folder path
set /p "GAME_DIR=Enter game folder path (e.g., C:\\Games\\MyGame): "

REM Input validation
if "%GAME_DIR%"=="" (
    echo.
    echo [ERROR] Game folder path was not entered.
    pause
    exit /b 1
)

REM Check game folder exists
if not exist "%GAME_DIR%" (
    echo.
    echo [ERROR] Game folder not found: %GAME_DIR%
    pause
    exit /b 1
)

echo.
echo ================================================
echo    Installation Ready
echo ================================================
echo Patch folder: %PATCH_DIR%
echo Game folder: %GAME_DIR%
echo.
echo The following operations will be performed:
echo 1. Copy data_languages folder
echo 2. Install SimpleLanguage.js plugin
echo 3. Backup and modify plugins.js
echo.

set /p "CONFIRM=Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo ================================================
echo    Installing patch...
echo ================================================

REM 1. Copy data_languages folder
echo.
echo [1/3] Copying data_languages folder...
if exist "%PATCH_DIR%data_languages" (
    xcopy /E /I /Y "%PATCH_DIR%data_languages" "%GAME_DIR%\\data_languages" >nul
    if errorlevel 1 (
        echo [ERROR] Failed to copy data_languages
        pause
        exit /b 1
    )
    echo [OK] data_languages copied successfully
) else (
    echo [WARNING] data_languages folder not found
)

REM 2. Install SimpleLanguage.js plugin
echo.
echo [2/3] Installing SimpleLanguage.js plugin...
if exist "%PATCH_DIR%js\\plugins\\SimpleLanguage.js" (
    if not exist "%GAME_DIR%\\js\\plugins" mkdir "%GAME_DIR%\\js\\plugins"
    copy /Y "%PATCH_DIR%js\\plugins\\SimpleLanguage.js" "%GAME_DIR%\\js\\plugins\\SimpleLanguage.js" >nul
    if errorlevel 1 (
        echo [ERROR] Failed to copy plugin
        pause
        exit /b 1
    )
    echo [OK] SimpleLanguage.js installed successfully
) else (
    echo [WARNING] SimpleLanguage.js file not found
)

REM 3. Backup and auto-modify plugins.js
echo.
echo [3/3] Configuring plugins.js...
if exist "%GAME_DIR%\\js\\plugins.js" (
    REM Create backup
    if not exist "%GAME_DIR%\\js\\plugins.js.backup" (
        copy /Y "%GAME_DIR%\\js\\plugins.js" "%GAME_DIR%\\js\\plugins.js.backup" >nul
        echo [OK] plugins.js backed up
    ) else (
        echo [INFO] plugins.js backup already exists
    )

    REM Auto-modify using PowerShell
    echo [INFO] Attempting automatic modification of plugins.js...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$file = '%GAME_DIR%\\js\\plugins.js'; ^
        $content = Get-Content $file -Raw -Encoding UTF8; ^
        if ($content -notmatch 'SimpleLanguage') { ^
            $newPlugin = '{\"\"name\"\":\"\"SimpleLanguage\"\",\"\"status\"\":true,\"\"description\"\":\"\"Multi-language support for the game\"\",\"\"parameters\"\":{\"\"languagesFolder\"\":\"\"data_languages\"\",\"\"defaultLanguage\"\":\"\"original\"\",\"\"availableLanguages\"\":\"\"original,ko\"\"}}'; ^
            $content = $content -replace '(\[)', ('$1' + [Environment]::NewLine + $newPlugin + ','); ^
            [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8); ^
            Write-Host '[OK] SimpleLanguage plugin added automatically' -ForegroundColor Green; ^
        } else { ^
            Write-Host '[INFO] SimpleLanguage plugin already exists' -ForegroundColor Yellow; ^
        }"

    if errorlevel 1 (
        echo.
        echo [WARNING] Automatic modification failed - manual editing required
        echo Please refer to plugins_js_guide_EN.txt for details.
    )
) else (
    REM Create new plugins.js if it doesn't exist
    echo [WARNING] plugins.js file not found
    echo [INFO] Creating new plugins.js file...

    if not exist "%GAME_DIR%\\js" mkdir "%GAME_DIR%\\js"

    (
        echo // Generated by RPG Maker.
        echo // Do not edit this file directly.
        echo var $plugins =
        echo [
        echo {"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}}
        echo ];
    ) > "%GAME_DIR%\\js\\plugins.js"

    if exist "%GAME_DIR%\\js\\plugins.js" (
        echo [OK] plugins.js file created successfully
    ) else (
        echo [ERROR] Failed to create plugins.js file
    )
)

echo.
echo ================================================
echo    Installation Complete!
echo ================================================
echo.
echo ✅ Installation completed successfully!
echo.
echo Next steps:
echo 1. Launch the game
echo 2. Check "Language / 언어" menu on the title screen
echo 3. You can change language in the Options menu
echo.
echo 💡 Note:
echo - plugins.js was configured automatically
echo - If you encounter issues, see plugins_js_guide_EN.txt
echo.
echo ⚠️ If problems occur:
echo - Copy js\\plugins.js.backup to js\\plugins.js to restore
echo - Delete data_languages folder
echo - Delete SimpleLanguage.js
echo.

pause
"""

    def _generate_install_bat_ja(self) -> str:
        """Japanese BAT file"""
        return """@echo off
chcp 65001 >nul
echo ================================================
echo    RPG Maker 翻訳パッチ 自動インストーラー
echo ================================================
echo.

REM 現在のフォルダ確認
set "PATCH_DIR=%~dp0"
echo パッチフォルダ: %PATCH_DIR%
echo.

REM ゲームフォルダパス入力
set /p "GAME_DIR=ゲームフォルダのパスを入力してください (例: C:\\Games\\MyGame): "

REM 入力確認
if "%GAME_DIR%"=="" (
    echo.
    echo [ERROR] ゲームフォルダのパスが入力されていません。
    pause
    exit /b 1
)

REM ゲームフォルダ存在確認
if not exist "%GAME_DIR%" (
    echo.
    echo [ERROR] ゲームフォルダが見つかりません: %GAME_DIR%
    pause
    exit /b 1
)

echo.
echo ================================================
echo    インストール準備完了
echo ================================================
echo パッチフォルダ: %PATCH_DIR%
echo ゲームフォルダ: %GAME_DIR%
echo.
echo 次の作業を実行します:
echo 1. data_languagesフォルダのコピー
echo 2. SimpleLanguage.jsプラグインのインストール
echo 3. plugins.jsのバックアップと変更
echo.

set /p "CONFIRM=続けますか? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo インストールがキャンセルされました。
    pause
    exit /b 0
)

echo.
echo ================================================
echo    パッチインストール中...
echo ================================================

REM 1. data_languagesフォルダコピー
echo.
echo [1/3] data_languagesフォルダをコピー中...
if exist "%PATCH_DIR%data_languages" (
    xcopy /E /I /Y "%PATCH_DIR%data_languages" "%GAME_DIR%\\data_languages" >nul
    if errorlevel 1 (
        echo [ERROR] data_languagesのコピーに失敗しました
        pause
        exit /b 1
    )
    echo [OK] data_languagesのコピーが完了しました
) else (
    echo [WARNING] data_languagesフォルダが見つかりません
)

REM 2. SimpleLanguage.jsプラグインインストール
echo.
echo [2/3] SimpleLanguage.jsプラグインをインストール中...
if exist "%PATCH_DIR%js\\plugins\\SimpleLanguage.js" (
    if not exist "%GAME_DIR%\\js\\plugins" mkdir "%GAME_DIR%\\js\\plugins"
    copy /Y "%PATCH_DIR%js\\plugins\\SimpleLanguage.js" "%GAME_DIR%\\js\\plugins\\SimpleLanguage.js" >nul
    if errorlevel 1 (
        echo [ERROR] プラグインのコピーに失敗しました
        pause
        exit /b 1
    )
    echo [OK] SimpleLanguage.jsのインストールが完了しました
) else (
    echo [WARNING] SimpleLanguage.jsファイルが見つかりません
)

REM 3. plugins.jsバックアップと自動変更
echo.
echo [3/3] plugins.jsを設定中...
if exist "%GAME_DIR%\\js\\plugins.js" (
    REM バックアップ作成
    if not exist "%GAME_DIR%\\js\\plugins.js.backup" (
        copy /Y "%GAME_DIR%\\js\\plugins.js" "%GAME_DIR%\\js\\plugins.js.backup" >nul
        echo [OK] plugins.jsのバックアップが完了しました
    ) else (
        echo [INFO] plugins.jsのバックアップは既に存在します
    )

    REM PowerShellで自動変更
    echo [INFO] plugins.jsの自動変更を試みています...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$file = '%GAME_DIR%\\js\\plugins.js'; ^
        $content = Get-Content $file -Raw -Encoding UTF8; ^
        if ($content -notmatch 'SimpleLanguage') { ^
            $newPlugin = '{\"\"name\"\":\"\"SimpleLanguage\"\",\"\"status\"\":true,\"\"description\"\":\"\"Multi-language support for the game\"\",\"\"parameters\"\":{\"\"languagesFolder\"\":\"\"data_languages\"\",\"\"defaultLanguage\"\":\"\"original\"\",\"\"availableLanguages\"\":\"\"original,ko\"\"}}'; ^
            $content = $content -replace '(\[)', ('$1' + [Environment]::NewLine + $newPlugin + ','); ^
            [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8); ^
            Write-Host '[OK] SimpleLanguageプラグインの自動追加が完了しました' -ForegroundColor Green; ^
        } else { ^
            Write-Host '[INFO] SimpleLanguageプラグインは既に存在します' -ForegroundColor Yellow; ^
        }"

    if errorlevel 1 (
        echo.
        echo [WARNING] 自動変更に失敗しました - 手動編集が必要です
        echo 詳細はplugins_js_guide_JA.txtを参照してください。
    )
) else (
    REM plugins.jsファイルがない場合は新規作成
    echo [WARNING] plugins.jsファイルが見つかりません
    echo [INFO] 新しいplugins.jsファイルを作成中...

    if not exist "%GAME_DIR%\\js" mkdir "%GAME_DIR%\\js"

    (
        echo // Generated by RPG Maker.
        echo // Do not edit this file directly.
        echo var $plugins =
        echo [
        echo {"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}}
        echo ];
    ) > "%GAME_DIR%\\js\\plugins.js"

    if exist "%GAME_DIR%\\js\\plugins.js" (
        echo [OK] plugins.jsファイルの作成が完了しました
    ) else (
        echo [ERROR] plugins.jsファイルの作成に失敗しました
    )
)

echo.
echo ================================================
echo    インストール完了!
echo ================================================
echo.
echo ✅ インストールが完了しました!
echo.
echo 次のステップ:
echo 1. ゲームを起動してください
echo 2. タイトル画面で「Language / 언어」メニューを確認
echo 3. オプションメニューで言語を変更できます
echo.
echo 💡 参考:
echo - plugins.jsは自動的に設定されました
echo - 問題が発生した場合はplugins_js_guide_JA.txtを参照
echo.
echo ⚠️ 問題が発生した場合:
echo - js\\plugins.js.backupをjs\\plugins.jsにコピーして復元
echo - data_languagesフォルダを削除
echo - SimpleLanguage.jsを削除
echo.

pause
"""

    def _generate_readme(self) -> str:
        """README 파일 생성 (다국어)"""
        return """=====================================================
    RPG Maker Translation Patch / 번역 패치 / 翻訳パッチ
=====================================================

[EN] This patch applies translation to RPG Maker games.
[KO] 이 패치는 RPG Maker 게임에 번역을 적용합니다.
[JA] このパッチはRPG Makerゲームに翻訳を適用します。

=====================================================
    Installation / 설치 방법 / インストール方法
=====================================================

【Method 1: Auto Install (Recommended) / 자동 설치 (권장) / 自動インストール (推奨)】

[EN] 1. Run INSTALL_PATCH_EN.bat
     2. Enter game folder path
     3. Automatic installation after confirmation

[KO] 1. INSTALL_PATCH_KO.bat 실행
     2. 게임 폴더 경로 입력
     3. 확인 후 자동 설치

[JA] 1. INSTALL_PATCH_JA.bat を実行
     2. ゲームフォルダのパスを入力
     3. 確認後、自動インストール

【Method 2: Manual Install / 수동 설치 / 手動インストール】

[EN] 1. Copy data_languages folder to game folder
     2. Copy js/plugins/SimpleLanguage.js to game's js/plugins/
     3. Modify js/plugins.js (see plugins_js_guide_EN.txt)

[KO] 1. data_languages 폴더를 게임 폴더에 복사
     2. js/plugins/SimpleLanguage.js를 게임의 js/plugins/에 복사
     3. js/plugins.js 수정 (plugins_js_guide_KO.txt 참고)

[JA] 1. data_languagesフォルダをゲームフォルダにコピー
     2. js/plugins/SimpleLanguage.jsをゲームのjs/plugins/にコピー
     3. js/plugins.jsを変更 (plugins_js_guide_JA.txt参照)

=====================================================
    File Structure / 파일 구조 / ファイル構造
=====================================================

translation_patch_YYYYMMDD/
├── data_languages/                # Translation data / 번역 데이터 / 翻訳データ
├── js/plugins/SimpleLanguage.js   # Plugin / 플러그인 / プラグイン
├── INSTALL_PATCH_KO.bat           # Korean installer / 한국어 설치 / 韓国語インストーラー
├── INSTALL_PATCH_EN.bat           # English installer / 영어 설치 / 英語インストーラー
├── INSTALL_PATCH_JA.bat           # Japanese installer / 일본어 설치 / 日本語インストーラー
├── plugins_js_guide_KO.txt        # Guide (Korean) / 가이드 (한국어)
├── plugins_js_guide_EN.txt        # Guide (English) / 가이드 (영어)
├── plugins_js_guide_JA.txt        # Guide (Japanese) / ガイド (日本語)
└── README.txt                     # This file / 이 파일 / このファイル

=====================================================
    After Running Game / 게임 실행 후 / ゲーム起動後
=====================================================

[EN] 1. Check "Language / 언어" menu on title screen
     2. Change language in Options menu
     3. Confirmation dialog when changing language

[KO] 1. 타이틀 화면에서 "Language / 언어" 메뉴 확인
     2. 옵션 메뉴에서 언어 변경 가능
     3. 언어 변경 시 확인 대화상자 표시

[JA] 1. タイトル画面で「Language / 언어」メニューを確認
     2. オプションメニューで言語変更可能
     3. 言語変更時に確認ダイアログが表示されます

=====================================================
    Troubleshooting / 문제 해결 / トラブルシューティング
=====================================================

【Game won't start / 게임이 시작되지 않을 때 / ゲームが起動しない】
[EN] - Copy js/plugins.js.backup to js/plugins.js
[KO] - js/plugins.js.backup을 js/plugins.js로 복사
[JA] - js/plugins.js.backupをjs/plugins.jsにコピー

【Translation not applied / 번역이 적용되지 않을 때 / 翻訳が適用されない】
[EN] - Press F12 to open Developer Tools and check Console
[KO] - F12를 눌러 개발자 도구를 열고 Console 확인
[JA] - F12を押して開発者ツールを開き、Consoleを確認

【Restore to original / 원본으로 되돌리기 / 元に戻す】
[EN] - Delete data_languages folder and SimpleLanguage.js
[KO] - data_languages 폴더와 SimpleLanguage.js 삭제
[JA] - data_languagesフォルダとSimpleLanguage.jsを削除

=====================================================
    License & Credits / 라이선스 및 크레딧 / ライセンスとクレジット
=====================================================

[EN] Generated by GameTranslator
[KO] GameTranslator로 생성되었습니다
[JA] GameTranslatorで生成されました

https://github.com/yourusername/gametranslator

SimpleLanguage Plugin: MIT License
Translation Data: See translator's license

=====================================================
"""

    def _generate_plugin_guide(self, lang: str = 'ko') -> str:
        """plugins.js 수정 가이드 생성"""
        if lang == 'en':
            return self._generate_plugin_guide_en()
        elif lang == 'ja':
            return self._generate_plugin_guide_ja()
        else:
            return self._generate_plugin_guide_ko()

    def _generate_plugin_guide_ko(self) -> str:
        """한국어 가이드"""
        return """=====================================================
    plugins.js 수정 가이드
=====================================================

【중요】
SimpleLanguage 플러그인이 정상 작동하려면 plugins.js 파일을
수정해야 합니다. 다른 모든 플러그인보다 먼저 로드되어야 합니다.

=====================================================
    수정 방법
=====================================================

1. 게임 폴더의 js/plugins.js 파일을 텍스트 에디터로 열기
   (메모장, VS Code, Notepad++ 등)

2. 다음과 같은 부분을 찾기:

   var $plugins =
   [
   {"name":"SomePlugin","status":true,...},
   {"name":"AnotherPlugin","status":true,...},
   ...

3. 첫 번째 플러그인 앞에 SimpleLanguage 추가:

   var $plugins =
   [
   {"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}},
   {"name":"SomePlugin","status":true,...},
   {"name":"AnotherPlugin","status":true,...},
   ...

4. 파일 저장

=====================================================
    예시: 수정 전
=====================================================

// Generated by RPG Maker.
// Do not edit this file directly.
var $plugins =
[
{"name":"LL_VariableWindow","status":true,"description":"変数を画面にウィンドウで表示します。","parameters":{}},
{"name":"PluginCommonBase","status":true,"description":"パラメータ解析を提供する共通基盤です","parameters":{}}
];

=====================================================
    예시: 수정 후
=====================================================

// Generated by RPG Maker.
// Do not edit this file directly.
var $plugins =
[
{"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}},
{"name":"LL_VariableWindow","status":true,"description":"変数を画面にウィンドウで表示します。","parameters":{}},
{"name":"PluginCommonBase","status":true,"description":"パラメータ解析を提供する共通基盤です","parameters":{}}
];

=====================================================
    주의사항
=====================================================

- SimpleLanguage는 반드시 첫 번째 플러그인이어야 합니다
- 쉼표(,) 위치에 주의하세요
- JSON 형식을 유지해야 합니다
- 백업(plugins.js.backup)을 먼저 만들어두세요

=====================================================
    확인 방법
=====================================================

1. 게임 실행
2. 타이틀 화면에서 "Language / 언어" 메뉴 확인
3. F12 눌러 개발자 도구 열기
4. Console에 오류가 없는지 확인

=====================================================
"""

    def _generate_plugin_guide_en(self) -> str:
        """English guide"""
        return """=====================================================
    plugins.js Modification Guide
=====================================================

【IMPORTANT】
For the SimpleLanguage plugin to work properly, you must modify
the plugins.js file. It must load before all other plugins.

=====================================================
    How to Modify
=====================================================

1. Open game_folder/js/plugins.js with a text editor
   (Notepad, VS Code, Notepad++, etc.)

2. Find this section:

   var $plugins =
   [
   {"name":"SomePlugin","status":true,...},
   {"name":"AnotherPlugin","status":true,...},
   ...

3. Add SimpleLanguage BEFORE the first plugin:

   var $plugins =
   [
   {"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}},
   {"name":"SomePlugin","status":true,...},
   {"name":"AnotherPlugin","status":true,...},
   ...

4. Save the file

=====================================================
    Important Notes
=====================================================

- SimpleLanguage MUST be the first plugin
- Pay attention to comma (,) placement
- Maintain JSON format
- Create backup (plugins.js.backup) first

=====================================================
    Verification
=====================================================

1. Run the game
2. Check "Language / 언어" menu on title screen
3. Press F12 to open Developer Tools
4. Check Console for errors

=====================================================
"""

    def _generate_plugin_guide_ja(self) -> str:
        """Japanese guide"""
        return """=====================================================
    plugins.js 変更ガイド
=====================================================

【重要】
SimpleLanguageプラグインが正常に動作するには、plugins.js
ファイルを変更する必要があります。他のすべてのプラグインより
先に読み込まれる必要があります。

=====================================================
    変更方法
=====================================================

1. game_folder/js/plugins.jsをテキストエディタで開く
   (メモ帳、VS Code、Notepad++など)

2. 次のような部分を探す:

   var $plugins =
   [
   {"name":"SomePlugin","status":true,...},
   {"name":"AnotherPlugin","status":true,...},
   ...

3. 最初のプラグインの前にSimpleLanguageを追加:

   var $plugins =
   [
   {"name":"SimpleLanguage","status":true,"description":"Multi-language support for the game","parameters":{"languagesFolder":"data_languages","defaultLanguage":"original","availableLanguages":"original,ko"}},
   {"name":"SomePlugin","status":true,...},
   {"name":"AnotherPlugin","status":true,...},
   ...

4. ファイルを保存

=====================================================
    注意事項
=====================================================

- SimpleLanguageは必ず最初のプラグインである必要があります
- カンマ(,)の位置に注意してください
- JSON形式を維持する必要があります
- バックアップ(plugins.js.backup)を先に作成してください

=====================================================
    確認方法
=====================================================

1. ゲームを起動
2. タイトル画面で「Language / 언어」メニューを確認
3. F12を押して開発者ツールを開く
4. Consoleにエラーがないか確認

=====================================================
"""
