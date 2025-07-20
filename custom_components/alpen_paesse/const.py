"""Constants for the Alpen-Paesse integration."""
from __future__ import annotations

DOMAIN = "alpen_paesse"

# Update interval in seconds (60 minutes)
UPDATE_INTERVAL = 3600

# Base URL for the website
BASE_URL = "https://alpen-paesse.ch/de/alpenpaesse"

# Available mountain passes with their URL paths and display names
AVAILABLE_PASSES = {
    "albulapass": {
        "name": "Albulapass",
        "url_path": "albulapass",
        "route": "Preda - La Punt Chamues-ch"
    },
    "berninapass": {
        "name": "Berninapass", 
        "url_path": "berninapass",
        "route": "Pontresina - San Carlo"
    },
    "bruenigpass": {
        "name": "Brünigpass",
        "url_path": "bruenigpass", 
        "route": "Lungern - Brienzwiler"
    },
    "flueelapass": {
        "name": "Flüelapass",
        "url_path": "flueelapass",
        "route": "Tschuggen - Susch"
    },
    "furkapass": {
        "name": "Furkapass",
        "url_path": "furkapass",
        "route": "Realp - Oberwald"
    },
    "forcola_di_livigno": {
        "name": "Forcola di Livigno",
        "url_path": "forcola-di-livigno",
        "route": "La Motta - Landesgrenze"
    },
    "glaubenbergpass": {
        "name": "Glaubenbergpass",
        "url_path": "glaubenbergpass",
        "route": "Sarnen - Entlebuch"
    },
    "glaubenbielenpass": {
        "name": "Glaubenbielenpass",
        "url_path": "glaubenbielenpass",
        "route": "Giswil - Sörenberg"
    },
    "gotthardpass": {
        "name": "Gotthardpass",
        "url_path": "gotthardpass",
        "route": "Göschenen - Airolo"
    },
    "grimselpass": {
        "name": "Grimselpass",
        "url_path": "grimselpass",
        "route": "Innertkirchen - Oberwald"
    },
    "grosser_st_bernhard": {
        "name": "Grosser St. Bernhard",
        "url_path": "grosser-st-bernhard",
        "route": "Bourg-Saint-Pierre - Landesgrenze"
    },
    "julierpass": {
        "name": "Julierpass",
        "url_path": "julierpass",
        "route": "Tiefencastel - Silvaplana"
    },
    "klausenpass": {
        "name": "Klausenpass",
        "url_path": "klausenpass",
        "route": "Altdorf - Linthal"
    },
    "lukmanierpass": {
        "name": "Lukmanierpass",
        "url_path": "lukmanierpass",
        "route": "Disentis - Biasca"
    },
    "malojapass": {
        "name": "Malojapass",
        "url_path": "malojapass",
        "route": "Silvaplana - Chiavenna"
    },
    "nufenenpass": {
        "name": "Nufenenpass",
        "url_path": "nufenenpass",
        "route": "Ulrichen - Airolo"
    },
    "oberalppass": {
        "name": "Oberalppass",
        "url_path": "oberalppass",
        "route": "Andermatt - Disentis"
    },
    "san_bernardino": {
        "name": "San Bernardino",
        "url_path": "san-bernardino",
        "route": "Splügen - Bellinzona"
    },
    "simplon": {
        "name": "Simplon",
        "url_path": "simplon",
        "route": "Brig - Domodossola"
    },
    "spluegenpass": {
        "name": "Splügenpass",
        "url_path": "spluegenpass", 
        "route": "Thusis - Chiavenna"
    },
    "sustenpass": {
        "name": "Sustenpass",
        "url_path": "sustenpass",
        "route": "Innertkirchen - Wassen"
    },
    "umbrailpass": {
        "name": "Umbrailpass",
        "url_path": "umbrailpass",
        "route": "Sta. Maria - Bormio"
    }
}

# Configuration keys
CONF_SELECTED_PASSES = "selected_passes"
CONF_LANGUAGE = "language"

# Language options
LANGUAGES = {
    "de": "Deutsch",
    "en": "English"
}
