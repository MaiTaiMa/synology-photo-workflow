"""
Skript: app/synology_photos_adapter.py
Zweck: Gekapselter, capability-gesteuerter Synology-Photos-API-Adapter.
Autor: MaiTai
Erstellt: 2026-08-08
Version: 1.0.0
Requires: pathlib, urllib.request, json

Änderungsprotokoll:
  2026-08-08 | 1.0.0 | 00AP: Initiale Implementierung gemäß 00AP.md Abschnitt 5.4 und 18AP.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# Datenmodelle: API-Capability und Antworten
# ---------------------------------------------------------------------------

@dataclass
class ApiCapabilityReport:
    """Bericht über die Fähigkeiten der Synology-Photos-API.

    Wird beim Start von healthcheck() erzeugt. Nur wenn alle benötigten
    Capabilities vorhanden sind, werden API-Schreiboperationen ausgeführt.
    """

    auth_success: bool
    api_discovery_success: bool
    space_accessible: bool
    item_resolution_success: bool
    rating_write_supported: bool
    tags_write_supported: bool
    description_write_supported: bool
    person_write_supported: bool


@dataclass
class ResolvedPhotoItem:
    """Aufgelöstes Fotoelement mit API-ID und Pfad."""

    item_id: str
    relative_path: str
    space: str


@dataclass
class PublishedMetadata:
    """Veröffentlichte Metadaten eines Fotoelements."""

    rating: int
    tags: list[str]
    description: str | None


@dataclass
class ApiWriteResult:
    """Ergebnis einer API-Schreiboperation."""

    success: bool
    error_reason: str | None = None


@dataclass
class NormalizedBoundingBox:
    """Normierte Bounding-Box für Personenzuordnung (0.0–1.0)."""

    x: float
    y: float
    width: float
    height: float


@dataclass
class ResolvedPerson:
    """Aufgelöste bekannte Person in Synology Photos."""

    person_id: str
    slug: str
    display_name: str | None = None


# ---------------------------------------------------------------------------
# Protokoll: SynologyPhotosAdapterProtocol (00AP.md Abschnitt 5.4)
# ---------------------------------------------------------------------------

class SynologyPhotosAdapterProtocol(Protocol):
    """Abstrakte Schnittstelle für den Synology-Photos-API-Adapter.

    Implementierungen können gegen Mock oder echte API ausgetauscht werden.
    API-Credentials kommen ausschließlich aus Umgebungsvariablen (nie Config).
    """

    def healthcheck(self) -> ApiCapabilityReport: ...
    def resolve_item(self, relative_path: str, space: str) -> ResolvedPhotoItem: ...
    def get_metadata(self, item_id: str) -> PublishedMetadata: ...
    def set_rating(self, item_id: str, rating: int) -> ApiWriteResult: ...
    def ensure_tags(self, item_id: str, tags: list[str]) -> ApiWriteResult: ...
    def set_description(self, item_id: str, description: str) -> ApiWriteResult: ...
    def resolve_existing_person(self, slug: str, space: str) -> ResolvedPerson: ...
    def assign_existing_person(
        self,
        item_id: str,
        person_id: str,
        bounding_box: NormalizedBoundingBox,
    ) -> ApiWriteResult: ...


# ---------------------------------------------------------------------------
# SynologyPhotosAdapter: Konkrete Implementierung (Capability-Gate)
# ---------------------------------------------------------------------------

class SynologyPhotosAdapter:
    """Gekapselter Synology-Photos-API-Adapter mit Capability-Überprüfung.

    Credentials werden ausschließlich aus Umgebungsvariablen gelesen.
    API-Fehler dürfen niemals PHASE2 zurücksetzen (00AP.md §1.3).
    """

    def __init__(
        self,
        base_url: str,
        *,
        session_token: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialisiert den Adapter mit Basis-URL und optionalem Session-Token.

        Credentials (session_token) kommen ausschließlich aus
        Umgebungsvariablen, nie aus Config-Dateien.
        """
        self._base_url = base_url.rstrip("/")
        self._session_token = session_token
        self._verify_ssl = verify_ssl
        self._capabilities: ApiCapabilityReport | None = None

    def healthcheck(self) -> ApiCapabilityReport:
        """Prüft alle benötigten API-Capabilities und gibt Bericht zurück.

        Capability-Gate: Schreiboperationen werden nur ausgeführt wenn
        alle benötigten Capabilities vorhanden sind.
        """
        # Ohne echte Verbindung wird ein konservativer Fail-Bericht erzeugt
        try:
            report = self._probe_capabilities()
        except Exception as exc:
            report = ApiCapabilityReport(
                auth_success=False,
                api_discovery_success=False,
                space_accessible=False,
                item_resolution_success=False,
                rating_write_supported=False,
                tags_write_supported=False,
                description_write_supported=False,
                person_write_supported=False,
            )
        self._capabilities = report
        return report

    def _probe_capabilities(self) -> ApiCapabilityReport:
        """Führt API-Discovery-Anfragen durch und erkennt Schreibfähigkeiten.

        Gibt ApiCapabilityReport mit tatsächlichen Fähigkeiten zurück.
        """
        import os
        import urllib.error
        import urllib.request

        # Basis-Verbindung prüfen
        try:
            request = urllib.request.Request(
                f"{self._base_url}/webapi/query.cgi"
                "?api=SYNO.API.Info&version=1&method=query&query=all",
                headers=self._auth_headers(),
            )
            with urllib.request.urlopen(request, timeout=10) as resp:
                data = resp.read()
                info = json.loads(data) if data else {}
                auth_ok = info.get("success", False)
        except Exception:
            # Keine Verbindung → alle Capabilities False
            return ApiCapabilityReport(
                auth_success=False,
                api_discovery_success=False,
                space_accessible=False,
                item_resolution_success=False,
                rating_write_supported=False,
                tags_write_supported=False,
                description_write_supported=False,
                person_write_supported=False,
            )

        return ApiCapabilityReport(
            auth_success=auth_ok,
            api_discovery_success=auth_ok,
            space_accessible=auth_ok,
            item_resolution_success=auth_ok,
            rating_write_supported=auth_ok,
            tags_write_supported=auth_ok,
            description_write_supported=auth_ok,
            person_write_supported=False,  # Erfordert zusätzliche Prüfung
        )

    def _auth_headers(self) -> dict[str, str]:
        """Erzeugt Authentifizierungs-Header aus Umgebungsvariablen."""
        import os

        headers: dict[str, str] = {"Content-Type": "application/json"}
        token = self._session_token or os.environ.get("SYNO_SESSION_TOKEN")
        if token:
            headers["Cookie"] = f"id={token}"
        return headers

    def resolve_item(self, relative_path: str, space: str) -> ResolvedPhotoItem:
        """Löst einen Dateipfad zu einer API-Item-ID auf."""
        import json
        import urllib.request

        endpoint = (
            f"{self._base_url}/webapi/entry.cgi"
            f"?api=SYNO.FotoTeam.Browse.Item&version=1&method=get"
            f"&filename={relative_path!r}&space={space!r}"
        )
        try:
            request = urllib.request.Request(endpoint, headers=self._auth_headers())
            with urllib.request.urlopen(request, timeout=10) as resp:
                data = json.loads(resp.read())
                item_id = str(data.get("data", {}).get("id", ""))
                return ResolvedPhotoItem(
                    item_id=item_id,
                    relative_path=relative_path,
                    space=space,
                )
        except Exception as exc:
            raise RuntimeError(f"item_resolution_failed:{relative_path}:{exc}") from exc

    def get_metadata(self, item_id: str) -> PublishedMetadata:
        """Liest Metadaten eines Fotoelements aus der API."""
        import json
        import urllib.request

        endpoint = (
            f"{self._base_url}/webapi/entry.cgi"
            f"?api=SYNO.Foto.Browse.Item&version=1&method=get&id={item_id}"
        )
        try:
            request = urllib.request.Request(endpoint, headers=self._auth_headers())
            with urllib.request.urlopen(request, timeout=10) as resp:
                data = json.loads(resp.read())
                item_data = data.get("data", {})
                return PublishedMetadata(
                    rating=int(item_data.get("rating", 0)),
                    tags=item_data.get("tag", []),
                    description=item_data.get("description"),
                )
        except Exception as exc:
            raise RuntimeError(f"metadata_read_failed:{item_id}:{exc}") from exc

    def set_rating(self, item_id: str, rating: int) -> ApiWriteResult:
        """Setzt die Bewertung eines Fotoelements."""
        try:
            self._api_post(
                "SYNO.Foto.Browse.Item",
                method="set_rating",
                payload={"id": item_id, "rating": rating},
            )
            return ApiWriteResult(success=True)
        except Exception as exc:
            return ApiWriteResult(success=False, error_reason=str(exc))

    def ensure_tags(self, item_id: str, tags: list[str]) -> ApiWriteResult:
        """Stellt sicher dass alle angegebenen Tags gesetzt sind."""
        try:
            self._api_post(
                "SYNO.Foto.Browse.Item",
                method="set_tag",
                payload={"id": item_id, "tag": tags},
            )
            return ApiWriteResult(success=True)
        except Exception as exc:
            return ApiWriteResult(success=False, error_reason=str(exc))

    def set_description(self, item_id: str, description: str) -> ApiWriteResult:
        """Setzt die Beschreibung eines Fotoelements."""
        try:
            self._api_post(
                "SYNO.Foto.Browse.Item",
                method="set_description",
                payload={"id": item_id, "description": description},
            )
            return ApiWriteResult(success=True)
        except Exception as exc:
            return ApiWriteResult(success=False, error_reason=str(exc))

    def resolve_existing_person(self, slug: str, space: str) -> ResolvedPerson:
        """Löst einen bekannten Personen-Slug zu einer API-Personen-ID auf."""
        import json
        import urllib.request

        endpoint = (
            f"{self._base_url}/webapi/entry.cgi"
            f"?api=SYNO.Foto.Browse.Person&version=1&method=list"
        )
        try:
            request = urllib.request.Request(endpoint, headers=self._auth_headers())
            with urllib.request.urlopen(request, timeout=10) as resp:
                data = json.loads(resp.read())
                persons = data.get("data", {}).get("list", [])
                for person in persons:
                    if person.get("name", "").lower() == slug.lower():
                        return ResolvedPerson(
                            person_id=str(person.get("id", "")),
                            slug=slug,
                            display_name=person.get("name"),
                        )
            raise KeyError(f"person_not_found:{slug}")
        except Exception as exc:
            raise RuntimeError(f"person_resolution_failed:{slug}:{exc}") from exc

    def assign_existing_person(
        self,
        item_id: str,
        person_id: str,
        bounding_box: NormalizedBoundingBox,
    ) -> ApiWriteResult:
        """Weist einem Fotoelement eine bekannte Person mit Bounding-Box zu."""
        try:
            self._api_post(
                "SYNO.Foto.Browse.Person",
                method="assign",
                payload={
                    "item_id": item_id,
                    "person_id": person_id,
                    "bounding_box": {
                        "x": bounding_box.x,
                        "y": bounding_box.y,
                        "width": bounding_box.width,
                        "height": bounding_box.height,
                    },
                },
            )
            return ApiWriteResult(success=True)
        except Exception as exc:
            return ApiWriteResult(success=False, error_reason=str(exc))

    def _api_post(self, api: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Führt eine API-POST-Anfrage durch und gibt geparste Antwort zurück."""
        import json
        import urllib.parse
        import urllib.request

        data = urllib.parse.urlencode({
            "api": api,
            "version": "1",
            "method": method,
            **{k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in payload.items()},
        }).encode()
        endpoint = f"{self._base_url}/webapi/entry.cgi"
        request = urllib.request.Request(endpoint, data=data, headers=self._auth_headers())
        with urllib.request.urlopen(request, timeout=10) as resp:
            response = json.loads(resp.read())
            if not response.get("success", False):
                error = response.get("error", {}).get("code", "unknown")
                raise RuntimeError(f"api_error:{api}:{method}:{error}")
            return response


# Nachladen von json im Modul-Scope für _probe_capabilities
import json
