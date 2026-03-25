import flet as ft

def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    page.add(
        ft.Text("🚀 ENDLICH! DIE APP LÄUFT!", size=35, color="green", weight="bold"),
        ft.Text("Der PC sendet direkt ans Handy.", size=20)
    )

# Der magische WLAN-Sender (ohne GitHub-Stress):
if __name__ == "__main__":
    ft.app(target=main, port=8560, host="0.0.0.0")
