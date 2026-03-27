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

## Uso

- No cabeçalho do taskboard aparece um botão com ícone ao lado do título (`h1`):
  - **🧹** — ativa a vista limpa  
  - **↺** — restaura o visual normal  
- O estado é guardado em `localStorage` (chave `taiga-clean-view`).

### Debug opcional

No console da página do Taiga:

```js
localStorage.setItem('taiga-clean-view-debug', '1');
location.reload();
```

Para desligar: `localStorage.removeItem('taiga-clean-view-debug'); location.reload();`

## Ficheiros

| Ficheiro | Descrição |
|----------|-----------|
| `taiga-clean-view.userscript.js` | Userscript pronto para colar no Tampermonkey |

## Licença

Este repositório é um projeto pessoal; ajusta a licença conforme precisares.
