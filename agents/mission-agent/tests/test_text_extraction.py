import httpx
import pytest

from mission_agent.text_extraction import recuperer_texte_url

_HTML = """
<html>
  <head><script>ignored();</script></head>
  <body>
    <nav>Menu</nav>
    <main>
      <h1>Développeur Python Freelance</h1>
      <p>Mission de 6 mois, TJM 550€/jour.</p>
    </main>
    <footer>Pied de page</footer>
  </body>
</html>
"""


def test_recuperer_texte_url_extrait_texte_html(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, text=_HTML, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    texte = recuperer_texte_url("https://example.com/annonce")

    assert "Développeur Python Freelance" in texte
    assert "Menu" not in texte
    assert "Pied de page" not in texte


def test_recuperer_texte_url_erreur_http_leve_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(404, text="introuvable", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(ValueError, match="--texte"):
        recuperer_texte_url("https://example.com/absent")


def test_recuperer_texte_url_page_sans_texte_leve_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        html_vide = "<html><script>x</script></html>"
        return httpx.Response(200, text=html_vide, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(ValueError, match="Aucun texte"):
        recuperer_texte_url("https://example.com/vide")
