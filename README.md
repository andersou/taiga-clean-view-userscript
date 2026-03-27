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
4. **Apague o modelo** que vier aberto e **cole o conteúdo completo** do arquivo `taiga-clean-view.userscript.js` (incluindo o bloco `// ==UserScript==` … `// ==/UserScript==`).
5. Salve (**Ctrl/Cmd+S** ou *File → Save*).
6. Acesse um taskboard do Taiga, por exemplo:  
   `https://tree.taiga.io/project/<seu-projeto>/taskboard/<sprint-slug>`  
   Recarregue a página se já estiver aberta.

Para atualizar depois de editar o ficheiro local: abra o mesmo script no dashboard, substitua o código e salve; a [documentação](https://www.tampermonkey.net/documentation.php) explica que `@version` entra no fluxo de verificação de atualização quando usas fontes remotas.

## Instalação (extensão Chrome — Manifest V3)

Na pasta [`extension/`](extension/) está uma extensão com o mesmo comportamento, usando [content scripts](https://developer.chrome.com/docs/extensions/mv3/content_scripts/) e `chrome.storage.local` para o estado.

1. Abre `chrome://extensions`.
2. Ativa **Modo do programador**.
3. **Carregar sem compactação** e escolhe a pasta `extension/` deste repositório.
4. Recarrega o taskboard do Taiga.

### Gerar `content.js` e o pacote `.zip` a partir do userscript

A fonte de verdade é `taiga-clean-view.userscript.js`. O script Python converte o corpo para extensão (`chrome.storage`, `async init`, etc.), atualiza o `manifest.json` com `@name`, `@version`, `@description`, `@author` e `@match`, e cria o ZIP em `dist/`.

Requisito: **Python 3**.

```bash
python3 scripts/build_extension.py
```

Saída:

- `extension/content.js` — **gerado** (não editar à mão; o ficheiro começa com um aviso)
- `extension/manifest.json` — atualizado (inclui variantes `.../taskboard` quando o header tem `.../taskboard/*`)
- `dist/taiga-clean-view-extension-<versão>.zip` — raiz do ZIP com `manifest.json` e `content.js` (pronto para carregar ou para a Chrome Web Store)

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

**Extensão** — o mesmo significado para a chave `taiga-clean-view-debug`, guardada em `chrome.storage.local`. Em desenvolvimento, o modo mais simples é definir temporariamente `debugEnabled = true` no arranque de `extension/content.js` ou usar *Detalhes da extensão → Armazenamento* no Chrome, quando disponível.

## Ficheiros

| Ficheiro | Descrição |
|----------|-----------|
| `taiga-clean-view.userscript.js` | Userscript pronto para colar no Tampermonkey |
| `scripts/build_extension.py` | Gera `extension/content.js`, manifest e ZIP em `dist/` |
| `extension/manifest.json` | Manifest V3 da extensão Chrome (gerado/atualizado pelo script) |
| `extension/content.js` | Content script (gerado pelo script a partir do userscript) |
| `dist/*.zip` | Pacote da extensão (após correr o script de build) |

## Licença

Este repositório é um projeto pessoal; ajusta a licença conforme precisares.
