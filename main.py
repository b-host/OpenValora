#!/usr/bin/env python3
"""
OpenValora - Aplicação Desktop Nativa & Servidor de Engenharia de Avaliações (NBR 14653).
Executa como janela desktop nativa ou servidor web local.
"""

import sys
import os
import socket
import threading
import time
import argparse
import webbrowser
import uvicorn
from app.main import app

def find_free_port(preferred: int = 8000) -> int:
    """Busca a porta preferencial ou uma porta livre disponível."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

def run_server(server: uvicorn.Server):
    """Executa o loop do Uvicorn no thread de suporte."""
    server.run()

def open_browser(port: int, host: str = "127.0.0.1"):
    time.sleep(1.2)
    url = f"http://{host}:{port}"
    print(f"\n[OpenValora] Abrindo navegador em {url} ...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[OpenValora] Aviso: Não foi possível abrir o navegador automaticamente: {e}")

def main():
    parser = argparse.ArgumentParser(description="OpenValora - Engenharia de Avaliações & Inferência Estatística")
    parser.add_argument("--server", action="store_true", help="Executa apenas como servidor web (sem abrir janela nativa)")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"), help="Endereço de escuta do servidor (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 0)), help="Porta do servidor (0 para detectar porta livre)")
    parser.add_argument("--no-browser", action="store_true", help="Não abre o navegador em modo servidor")
    args = parser.parse_args()

    port = args.port if args.port > 0 else find_free_port(8000)
    host = args.host

    print("=" * 65)
    print("  OpenValora - Software de Engenharia de Avaliações")
    print("  Inferência Estatística, Regressão Linear & RNA (NBR 14653)")
    print("=" * 65)
    print(f"  Serviço local rodando em: http://{host}:{port}")

    # Configura e inicia o servidor Uvicorn em background
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=run_server, args=(server,), daemon=True)
    server_thread.start()

    # Dá tempo para o servidor iniciar
    time.sleep(0.5)

    # Modo 1: Servidor puro (ex.: Docker, servidor headless ou argumento --server)
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER") == "1"
    is_headless = not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")

    if args.server or is_docker or is_headless:
        print("  Modo: Servidor Web Local / Docker")
        print("  Pressione Ctrl+C para encerrar.")
        print("=" * 65)
        if not args.no_browser and not is_docker and not is_headless:
            threading.Thread(target=open_browser, args=(port, host), daemon=True).start()
        try:
            while server_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[OpenValora] Encerrando servidor...")
            server.should_exit = True
        sys.exit(0)

    # Modo 2: Janela Desktop Nativa (padrão para aplicativo desktop e AppImage)
    print("  Modo: Aplicativo Desktop Nativo")
    print("  Feche a janela para encerrar o aplicativo.")
    print("=" * 65)

    # Configurações de ambiente essenciais para estabilidade universal no Linux (Wayland, X11, NVIDIA, AMD, Intel)
    if sys.platform.startswith("linux"):
        # Previne falha do renderizador DMABuf no WebKitGTK com drivers NVIDIA / Wayland
        os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")
        # Desativa sandbox bwrap que falha em sistemas imutáveis/OSTree (Fedora Silverblue, Bluefin) ou containers
        os.environ.setdefault("WEBKIT_FORCE_SANDBOX", "0")
        os.environ.setdefault("WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS", "1")

    gui_success = False
    try:
        import webview

        # Permite download de relatórios/arquivos e redirecionamento de links externos
        webview.settings['ALLOW_DOWNLOADS'] = True
        webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True

        # Diretório persistente para armazenamento local e cache WebKit/WebView2
        if sys.platform.startswith("win"):
            base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            storage_dir = os.path.join(base_dir, "OpenValora", "webview")
        else:
            storage_dir = os.path.join(os.path.expanduser("~"), ".config", "openvalora", "webview")
        os.makedirs(storage_dir, exist_ok=True)

        # Determina ícone oficial da janela (OpenValora.png)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        app_icon = None
        if sys.platform.startswith("win"):
            icon_candidates = [
                os.path.join(base_path, "packaging", "openvalora.ico"),
                os.path.join(base_path, "packaging", "valoraopen.ico"),
                os.path.join(base_path, "OpenValora.png"),
                os.path.join(base_path, "ValoraOpen.png"),
            ]
        else:
            # No Linux (GNOME/Wayland/X11), utiliza exclusivamente PNG para evitar erro de decodificação no gdk-pixbuf/glycin
            icon_candidates = [
                os.path.join(base_path, "OpenValora.png"),
                os.path.join(base_path, "ValoraOpen.png"),
                os.path.join(base_path, "packaging", "OpenValora.png"),
                os.path.join(base_path, "packaging", "openvalora.png"),
                os.path.join(base_path, "packaging", "ValoraOpen.png"),
                os.path.join(base_path, "packaging", "valoraopen.png"),
            ]
        for candidate in icon_candidates:
            if os.path.exists(candidate):
                app_icon = candidate
                break

        # Configurações GTK no Linux (Wayland e X11) para exibir o ícone no dock/painel/taskbar
        if sys.platform.startswith("linux"):
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk, GLib
                GLib.set_prgname("openvalora")
                GLib.set_application_name("OpenValora")
                if app_icon and os.path.exists(app_icon):
                    try:
                        Gtk.Window.set_default_icon_from_file(app_icon)
                    except Exception:
                        pass
            except Exception:
                pass

        # Inicializa a janela nativa do OpenValora
        window = webview.create_window(
            title="OpenValora - Engenharia de Avaliações (NBR 14653)",
            url=f"http://127.0.0.1:{port}",
            width=1320,
            height=860,
            min_size=(960, 640),
            text_select=True,
            confirm_close=False,
        )
        # Bloqueia até que a janela seja fechada pelo usuário
        webview.start(private_mode=False, storage_path=storage_dir, icon=app_icon)
        gui_success = True

    except Exception as e:
        print(f"[OpenValora] Aviso: Não foi possível abrir a janela nativa ({e}).")

        # Tentativa de fallback para X11/XWayland no Linux caso o Wayland nativo falhe
        if sys.platform.startswith("linux") and os.environ.get("GDK_BACKEND") != "x11":
            try:
                print("[OpenValora] Tentando fallback para backend X11/XWayland...")
                os.environ["GDK_BACKEND"] = "x11"
                import webview
                window = webview.create_window(
                    title="OpenValora - Engenharia de Avaliações (NBR 14653)",
                    url=f"http://127.0.0.1:{port}",
                    width=1320,
                    height=860,
                    min_size=(960, 640),
                    text_select=True,
                    confirm_close=False,
                )
                webview.start(private_mode=False, storage_path=storage_dir, icon=app_icon)
                gui_success = True
            except Exception as e2:
                print(f"[OpenValora] Aviso: Fallback X11 também indisponível ({e2}).")

    # Se a GUI nativa abriu e fechou normalmente pelo usuário, encerra o servidor
    if gui_success:
        print("\n[OpenValora] Janela encerrada pelo usuário. Finalizando...")
        server.should_exit = True
        sys.exit(0)
    else:
        # Fallback de segurança definitivo: Abre no navegador padrão e MANTÉM o servidor ativo
        print("\n" + "=" * 65)
        print("  [OpenValora] MODO DE SEGURANÇA: Interface aberta no navegador padrão")
        print(f"  Acesse em: http://{host}:{port}")
        print("  Pressione Ctrl+C no terminal para encerrar.")
        print("=" * 65 + "\n")
        open_browser(port, host)
        try:
            while server_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[OpenValora] Encerrando servidor...")
            server.should_exit = True
            sys.exit(0)

if __name__ == "__main__":
    main()
