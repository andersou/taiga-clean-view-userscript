# Taiga Taskboard – Clean view

Userscript para o [Taiga](https://www.taiga.io/) que reduz o ruído visual no taskboard (resumo grande, espaçamentos) e oferece um botão com ícone para alternar entre **vista limpa** e **restaurar**.

## Pré-requisitos

- Navegador compatível com extensões
- [Tampermonkey](https://www.tampermonkey.net/) (ou outro gestor de userscripts com suporte a `@match` e cabeçalho `// ==UserScript==`)

A documentação oficial de metadados (`@match`, `@grant`, `@run-at`, etc.) está em [Tampermonkey – Documentation](https://www.tampermonkey.net/documentation.php).

## Instalação (Tampermonkey)

1. **Instale a extensão** a partir do site oficial: [tampermonkey.net](https://www.tampermonkey.net/).
2. Abra o **Dashboard** do Tampermonkey (ícone da extensão → *Dashboard*).
3. Crie um script novo:
   - *Create a new script…* (ou equivalente no seu idioma).
4. Rode o build e use o arquivo gerado em `dist/taiga-clean-view.userscript.js`.
5. **Apague o modelo** que vier aberto e **cole o conteúdo completo** do userscript gerado (incluindo o bloco `// ==UserScript==` … `// ==/UserScript==`).
6. Salve (**Ctrl/Cmd+S** ou *File → Save*).
7. Acesse um taskboard do Taiga, por exemplo:  
   `https://tree.taiga.io/project/<seu-projeto>/taskboard/<sprint-slug>`  
   Recarregue a página se já estiver aberta.

Para atualizar depois de editar o ficheiro local: abra o mesmo script no dashboard, substitua o código e salve; a [documentação](https://www.tampermonkey.net/documentation.php) explica que `@version` entra no fluxo de verificação de atualização quando usas fontes remotas.

## Instalação (extensão Chrome — Manifest V3)

Depois de correr o build, a pasta [`generated/extension/`](generated/extension/) contém a extensão (Manifest V3), com [content scripts](https://developer.chrome.com/docs/extensions/mv3/content_scripts/) e `chrome.storage.local` para o estado.

1. Abre `chrome://extensions`.
2. Ativa **Modo do programador**.
3. **Carregar sem compactação** e escolhe a pasta `generated/extension/` deste repositório (criada pelo build).
4. Recarrega o taskboard do Taiga.

### Gerar `userscript` e `content.js` a partir de `src/`

A arquitetura usa um núcleo compartilhado em `src/`:

- `src/core.js` (lógica de UI e comportamento)
- `src/storage.localstorage.js` (adapter do userscript)
- `src/storage.chrome.js` (adapter da extensão)
- `src/entry.userscript.js` e `src/entry.extension.js` (bootstraps)

O script Python concatena estes módulos, lê o cabeçalho Tampermonkey de `src/userscript.header.js` e gera `generated/extension/content.js` e `generated/extension/manifest.json`. **A geração de `.crx` está desativada** no script (sideload local é restrito em muitos navegadores; usa *Carregar sem compactação* em `generated/extension/` ou `--zip` para a loja).

Requisitos: **Python 3** (stdlib chega para o build padrão):

```bash
python3 scripts/build_extension.py
```

Opcional: **`--zip`** — gera também `dist/*.zip` (formato da **Chrome Web Store**).

Para voltar a **empacotar CRX3** localmente, descomenta o bloco em `scripts/build_extension.py` (função `write_crx_artifact`) e instala `pip install -r scripts/requirements.txt` (`cryptography` + `scripts/crx3_pack.py`).

Saída:

- `dist/taiga-clean-view.userscript.js` — **gerado** (usa header de `src/userscript.header.js`)
- `generated/extension/content.js` — **gerado** (não editar à mão; pasta ignorada pelo git)
- `generated/extension/manifest.json` — **gerado**

**Nota:** em muitos sistemas o Chrome só instala `.crx` local com **modo de programador** ligado e [limitações por plataforma](https://developer.chrome.com/docs/extensions/how-to/distribute/install-extensions); para desenvolvimento costuma ser mais simples *Carregar sem compactação* na pasta `generated/extension/`.

### Erro «CRX header invalid»

Aparece se o ficheiro for um **ZIP mal disfarçado** (primeiros bytes `PK`). Um CRX válido começa com `Cr24`. Se gerares CRX manualmente ou reativares o passo no build, instala as dependências em `scripts/requirements.txt`.

## Uso

- No cabeçalho do taskboard aparece um botão com ícone ao lado do título (`h1`):
  - **🧹** — ativa a vista limpa  
  - **↺** — restaura o visual normal  
- **Userscript:** estado em `localStorage` do site (chave `taiga-clean-view`).
- **Extensão:** estado em `chrome.storage.local` (mesma chave; sincroniza entre abas).

### Debug opcional

**Userscript** — no console da página do Taiga:

```js
localStorage.setItem('taiga-clean-view-debug', '1');
location.reload();
```

Para desligar: `localStorage.removeItem('taiga-clean-view-debug'); location.reload();`

**Extensão** — o mesmo significado para a chave `taiga-clean-view-debug`, guardada em `chrome.storage.local`. Em desenvolvimento, o modo mais simples é editar `src/core.js` temporariamente ou usar *Detalhes da extensão → Armazenamento* no Chrome, quando disponível.

## Ficheiros

| Ficheiro | Descrição |
|----------|-----------|
| `src/core.js` | Núcleo compartilhado de comportamento |
| `src/storage.localstorage.js` | Adapter de persistência do userscript |
| `src/storage.chrome.js` | Adapter de persistência da extensão |
| `src/entry.userscript.js` | Bootstrap do userscript |
| `src/entry.extension.js` | Bootstrap do content script |
| `src/userscript.header.js` | Header metadata do userscript (fonte para o build) |
| `scripts/build_extension.py` | Gera userscript, content script e manifest (opcional `--zip`; CRX desativado no script) |
| `scripts/crx3_pack.py` | Empacota bytes ZIP → CRX3 (só se reativares CRX no build) |
| `scripts/requirements.txt` | `cryptography` para assinar CRX (só se usares `crx3_pack`) |
| `keys/dev-signing-key.pem` | Chave PEM local para CRX (opcional; não versionar) |
| `generated/extension/manifest.json` | Manifest V3 (gerado pelo build; não versionar) |
| `generated/extension/content.js` | Content script (gerado pelo build; não versionar) |
| `dist/taiga-clean-view.userscript.js` | Userscript final gerado para Tampermonkey |
| `dist/*.zip` | Opcional: pacote para a Chrome Web Store (`python3 scripts/build_extension.py --zip`) |

## Licença

Este repositório é um projeto pessoal; ajusta a licença conforme precisares.
