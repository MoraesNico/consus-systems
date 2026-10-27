# Assets de terceiros vendorizados

Servidos localmente pelo WhiteNoise (constituição, princípio V — sem CDN em execução).

| Asset | Arquivo | Origem | Versão | Licença | SHA-256 |
|-------|---------|--------|--------|---------|---------|
| HTMX | `vendor/htmx.min.js` | npm `htmx.org` (`dist/htmx.min.js`) | 2.0.11 | 0BSD | `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717` |
| IBM Plex Sans Regular | `fonts/IBMPlexSans-Regular-Latin1.woff2` | npm `@ibm/plex-sans` (`fonts/split/woff2`) — release oficial IBM/plex | 1.1.0 | SIL OFL 1.1 (`fonts/OFL.txt`) | `b5ad7bd39f996144915f0ad9849a90183b27d8c28ad97ed98af5b1bebc51f6b1` |
| IBM Plex Sans Medium | `fonts/IBMPlexSans-Medium-Latin1.woff2` | idem | 1.1.0 | SIL OFL 1.1 | `b5610af04d0d4b5a14a621d96d974b993e945a065db1a8861918f69ef9321934` |
| IBM Plex Sans SemiBold | `fonts/IBMPlexSans-SemiBold-Latin1.woff2` | idem | 1.1.0 | SIL OFL 1.1 | `fff0ab3a88b0b4aa0b693e4f0201359a15183b08e3fa5696d1918d8f0ade8ad5` |
| IBM Plex Mono Regular | `fonts/IBMPlexMono-Regular-Latin1.woff2` | npm `@ibm/plex-mono` (`fonts/split/woff2`) | 2.5.0 | SIL OFL 1.1 | `e8993d946649b9d01abb1ed06d574b19d8ea3e66b5c3948602db335c44c18e56` |
| IBM Plex Mono SemiBold | `fonts/IBMPlexMono-SemiBold-Latin1.woff2` | idem | 2.5.0 | SIL OFL 1.1 | `b7acd05041ab65f3b7039e218ddd893065e11a07e85ea85019473152a51b6b7d` |
| Ícones Lucide (subset) | `vendor/lucide/sprite.svg` | npm `lucide-static` (`icons/*.svg`, 23 ícones de design-system §2.13 + 17 da Parte 2) | 1.60.0 | ISC (`vendor/lucide/LICENSE`) | `3b236334cc263c52dcdc24128c7c5ab14dd0bab11350d36033ea6db466577e16` |

O sprite é gerado a partir dos SVGs individuais: cada ícone vira um `<symbol id="<nome>"
viewBox="0 0 24 24">` sem atributos de cor/traço (definidos em `.icone`, `components.css`).
