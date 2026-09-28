"""Impianto comune delle prove di Dadillo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5.5, UltraCode.

Il desktop nascosto, dalla 2.11.4, sul modello di tests/conftest.py di
Tornello 10.13.37. Diverse prove creano finestre wx, e Windows da' il primo
piano anche a una finestra mai mostrata quando riceve il fuoco, perche' il
processo di pytest e' partito dal terminale che aveva il primo piano: il 26
settembre 2026 finestre invisibili delle prove di Tornello hanno preso il
primo piano sullo schermo di Gabriele, e NVDA gli leggeva i loro titoli.
Percio', prima che wx crei qualunque finestra, il thread principale passa su
un desktop di Windows tutto suo, che nessuno vede: le finestre nascono li',
dove fuoco, attivazione e primo piano funzionano come sullo schermo ma non
toccano quello di chi lancia le prove. Se il passaggio non riesce, la suite
non parte: meglio nessuna prova che finestre sul desktop vero. Fuori da
Windows non serve.
"""

import os
import sys

import pytest

NOME_DEL_DESKTOP = f"dadillo_prove_{os.getpid()}"
GENERIC_ALL = 0x10000000
# La maniglia del desktop nascosto resta aperta finche' il processo vive:
# chiusa, il desktop sparirebbe sotto le finestre delle prove.
DESKTOP_DELLE_PROVE = {}


def _user32_del_desktop():
    """user32 con le firme delle funzioni dei desktop. Una copia tutta sua,
    cosi' le firme non cambiano quelle che il resto del processo usa."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.CreateDesktopW.restype = wintypes.HANDLE
    user32.CreateDesktopW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    user32.SetThreadDesktop.restype = wintypes.BOOL
    user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
    user32.CloseDesktop.restype = wintypes.BOOL
    user32.CloseDesktop.argtypes = [wintypes.HANDLE]
    return user32


def _desktop_non_disponibile(azione, funzione, codice):
    import ctypes

    return (
        f"Le prove non partono: non si e' potuto {azione} ({funzione}, errore "
        f"di Windows {codice}: {ctypes.FormatError(codice).strip()}). Le "
        "finestre delle prove nascono su un desktop di Windows nascosto: "
        "senza, una finestra che riceve il fuoco prenderebbe il primo piano "
        "sullo schermo di chi lancia le prove. Il passaggio fallisce se "
        "questo thread ha gia' delle finestre."
    )


def pytest_configure(config):
    """Il passaggio al desktop nascosto, una volta per processo, prima che
    le prove importino wx e creino la prima finestra. Qui si dichiara anche
    il segno finestre_vere."""
    config.addinivalue_line(
        "markers",
        "finestre_vere: la prova mostra finestre vere, possibile solo sul desktop nascosto",
    )
    if sys.platform != "win32" or DESKTOP_DELLE_PROVE:
        return
    import ctypes

    user32 = _user32_del_desktop()
    desktop = user32.CreateDesktopW(NOME_DEL_DESKTOP, None, None, 0, GENERIC_ALL, None)
    if not desktop:
        raise pytest.UsageError(
            _desktop_non_disponibile(
                "creare il desktop nascosto", "CreateDesktopW", ctypes.get_last_error()
            )
        )
    if not user32.SetThreadDesktop(desktop):
        codice = ctypes.get_last_error()
        user32.CloseDesktop(desktop)
        raise pytest.UsageError(
            _desktop_non_disponibile(
                "spostare le prove sul desktop nascosto", "SetThreadDesktop", codice
            )
        )
    DESKTOP_DELLE_PROVE["nascosto"] = desktop
