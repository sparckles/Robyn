const codeActionButtons = [
  {
    icon: 'copy',
    id: 'copy',
    title: 'Copy Code',
    show: true
  },
  {
    icon: 'order',
    id: 'lines',
    title: 'Toggle Line Numbers',
    show: true
  },
  {
    icon: 'carly',
    id: 'wrap',
    title: 'Toggle Line Wrap',
    show: false
  },
  {
    icon: 'expand',
    id: 'expand',
    title: 'Toggle code block expand',
    show: false
  }
];

const body = elem('body');
const maxLines = codeBlockConfig.maximum;
const showLines = codeBlockConfig.show;
const copyId = 'panel_copy';
const wrapId = 'panel_wrap';
const linesId = 'panel_lines';
const panelExpand = 'panel_expand';
const panelExpanded = 'panel_expanded';
const panelHide = 'panel_hide';
const panelFrom = 'panel_from';
const panelBox = 'panel_box';
const fullHeight = 'initial';
const highlightWrap = 'highlight_wrap'
const highlight = 'highlight';

function wrapOrphanedPreElements() {
  const pres = elems('pre');
  Array.from(pres).forEach(function(pre){
    const parent = pre.parentNode;
    const isOrpaned = !containsClass(parent, highlight) ;
    if(isOrpaned) {
      const preWrapper = createEl();
      preWrapper.className = highlight;
      const outerWrapper = createEl();
      outerWrapper.className = highlightWrap;
      wrapEl(pre, preWrapper);
      wrapEl(preWrapper, outerWrapper);
    }
  })
  /*
  @Todo
  1. Add UI control to orphaned blocks
  */
}

wrapOrphanedPreElements();

function codeBlocks() {
  const markedCodeBlocks = elems('code');
  const blocks = Array.from(markedCodeBlocks).filter(function(block){
    return block.closest("pre") && !Array.from(block.classList).includes('noClass');
  }).map(function(block){
    return block
  });
  return blocks;
}

function codeBlockFits(block) {
  // return false if codeblock overflows
  const blockWidth = block.offsetWidth;
  const highlightBlockWidth = block.closest(`.${highlight}`).offsetWidth;
  return blockWidth <= highlightBlockWidth ? true : false;
}

function maxHeightIsSet(elem) {
  let maxHeight = elem.style.maxHeight;
  return maxHeight.includes('px')
}

function restrainCodeBlockHeight(lines) {
  const lastLine = lines[maxLines-1];
  let maxCodeBlockHeight = fullHeight;
  if(lastLine) {
    const lastLinePos = lastLine.offsetTop;
    if(lastLinePos !== 0) {
      maxCodeBlockHeight = `${lastLinePos}px`;
      const codeBlock = lines[0].parentNode;
      const outerBlock = codeBlock.closest(`.${highlight}`);
      const isExpanded = containsClass(outerBlock, panelExpanded);
      if(!isExpanded) {
        codeBlock.dataset.height = maxCodeBlockHeight;
        codeBlock.style.maxHeight = maxCodeBlockHeight;
      }
    }
  }
}

const blocks = codeBlocks();

function collapseCodeBlock(block) {
  const lines = elems('.ln', block);
  const codeLines = lines.length;
  if(!lines) {
    // hide lines toggle button for blocks that have no lines.
    setTimeout(() => {
      let panelLinesParentEl = block.closest(`.${highlightWrap}`);
      let panelLinesEl = elem(`.${linesId}`, panelLinesParentEl);
      pushClass(panelLinesEl, panelHide);
    }, 2000)
  }
  if (codeLines > maxLines) {
    const expandDot = createEl()
    pushClass(expandDot, panelExpand);
    pushClass(expandDot, panelFrom);
    expandDot.title = "Toggle code block expand";
    expandDot.textContent = "...";
    const outerBlock = block.closest(`.${highlight}`);
    window.setTimeout(function(){
      const expandIcon = outerBlock.nextElementSibling.lastElementChild;
      deleteClass(expandIcon, panelHide);
    }, 150)

    restrainCodeBlockHeight(lines);
    const highlightElement = block.parentNode.parentNode;
    highlightElement.appendChild(expandDot);
  }
}

blocks.forEach(function(block){
  collapseCodeBlock(block);
})

function actionPanel() {
  const panel = createEl();
  panel.className = panelBox;

  codeActionButtons.forEach(function(button) {
    // create button
    const btn = createEl('a');
    btn.href = '#';
    btn.title = button.title;
    btn.className = `icon panel_icon panel_${button.id}`;
    button.show ? false : pushClass(btn, panelHide);
    // load icon inside button
    loadSvg(button.icon, btn);
    // append button on panel
    panel.appendChild(btn);
  });

  return panel;
}

function toggleLineNumbers(elems) {
  if(elems) {
    elems.forEach(function (elem, index) {
      // mark the code element when there are no lines
      modifyClass(elem, 'pre_nolines')
    });
    restrainCodeBlockHeight(elems);
  }
}

function toggleLineWrap(elem) {
  modifyClass(elem, 'pre_wrap');
  // retain max number of code lines on line wrap
  const lines = elems('.ln', elem);
  restrainCodeBlockHeight(lines);
}

function copyCode(codeElement) {
  const codeElementClone = codeElement.cloneNode(true);
  const copyBtn = codeElement.parentNode.parentNode.querySelector(`.${copyId}`);
  const originalTitle = copyBtn.title;
  loadSvg('check', copyBtn);
  copyBtn.title = 'Code Copied';

  lineNumbers = elems('.ln', codeElementClone);
  // remove line numbers before copying
  if(lineNumbers.length) {
    lineNumbers.forEach(function(line){
      line.remove();
    });
  }

  // copy code
  copyToClipboard(codeElementClone.textContent);

  setTimeout(function() {
    copyBtn.title = originalTitle;
    loadSvg('copy', copyBtn);
  }, 2250);
}

function disableCodeLineNumbers(block){
  const lines = elems('.ln', block)
  toggleLineNumbers(lines);
}

(function codeActions(){
  const blocks = codeBlocks();

  const highlightWrapId = highlightWrap;
  blocks.forEach(function(block){
    // disable line numbers if disabled globally
    showLines === false ? disableCodeLineNumbers(block) : false;

    const highlightElement = block.parentNode.parentNode;
    // wrap code block in a div
    const highlightWrapper = createEl();
    highlightWrapper.className = highlightWrapId;

    wrapEl(highlightElement, highlightWrapper);

    const panel = actionPanel();
    // show wrap icon only if the code block needs wrapping
    const wrapIcon = elem(`.${wrapId}`, panel);
    codeBlockFits(block) ? false : deleteClass(wrapIcon, panelHide);

    // append buttons
    highlightWrapper.appendChild(panel);
  });

  function isItem(target, id) {
    // if is item or within item
    return target.matches(`.${id}`) || target.closest(`.${id}`);
  }

  function showActive(target, targetClass) {
    const targetElement = target.matches(`.${targetClass}`) ? target : target.closest(`.${targetClass}`);

    deleteClass(targetElement, active);
    setTimeout(function() {
      modifyClass(targetElement, active)
    }, 50)
  }

  doc.addEventListener('click', function(event){
    // copy code block
    const target = event.target;
    const isCopyIcon = isItem(target, copyId);
    const isWrapIcon = isItem(target, wrapId);
    const isLinesIcon = isItem(target, linesId);
    const isExpandIcon = isItem(target, panelExpand);
    const isActionable = isCopyIcon || isWrapIcon || isLinesIcon || isExpandIcon;

    if(isActionable) {
      event.preventDefault();
      showActive(target, 'icon');
      const codeElement = target.closest(`.${highlightWrapId}`).firstElementChild.firstElementChild;
      let lineNumbers = elems('.ln', codeElement);

      isWrapIcon ? toggleLineWrap(codeElement) : false;

      isLinesIcon ? toggleLineNumbers(lineNumbers) : false;

      if (isExpandIcon) {
        let thisCodeBlock = codeElement.firstElementChild;
        const outerBlock = thisCodeBlock.closest('.highlight');
        if(maxHeightIsSet(thisCodeBlock)) {
          thisCodeBlock.style.maxHeight = fullHeight;
          // mark code block as expanded
          pushClass(outerBlock, panelExpanded)
        } else {
          thisCodeBlock.style.maxHeight = thisCodeBlock.dataset.height;
          // unmark code block as expanded
          deleteClass(outerBlock, panelExpanded)
        }
      }

      if(isCopyIcon) copyCode(codeElement);
    }
  });

  (function addLangLabel() {
    const blocks = codeBlocks();
    blocks.forEach(function(block){
      let label = block.dataset.lang;
      label = label === 'sh' ? 'bash' : label;
      if(label !== "fallback") {
        const labelEl = createEl();
        labelEl.textContent = label;
        pushClass(labelEl, 'lang');
        block.closest(`.${highlightWrap}`).appendChild(labelEl);
      }
    });
  })();
})();
