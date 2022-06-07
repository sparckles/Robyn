(function calcNavHeight(){
  const nav = elem('.nav_header');
  const navHeight = nav.offsetHeight + 25;
  return navHeight;
})();

function toggleMenu(event) {
  const target = event.target;
  const isToggleControl = target.matches(`.${toggleId}`);
  const isWithToggleControl = target.closest(`.${toggleId}`);
  const showInstances = elems(`.${showId}`) ? Array.from(elems(`.${showId}`)) : [];
  const menuInstance = target.closest(`.${menu}`);

  function showOff(target, self = false) {
    showInstances.forEach(function(showInstance){
      if(!self) {
        deleteClass(showInstance, showId);
      }
      if(showInstance !== target.closest(`.${menu}`)) {
        deleteClass(showInstance, showId);
      }
    });
  }

  if(isToggleControl || isWithToggleControl) {
    const menu = isWithToggleControl ? isWithToggleControl.parentNode.parentNode : target.parentNode.parentNode;
    event.preventDefault();
    modifyClass(menu, showId);
  } else {
    if(!menuInstance) {
      showOff(target);
    } else {
      showOff(target, true);
    }
  }
}

(function markInlineCodeTags(){
  const codeBlocks = elems('code');
  if(codeBlocks) {
    codeBlocks.forEach(function(codeBlock){
      if(!hasClasses(codeBlock)) {
        codeBlock.children.length ? false : pushClass(codeBlock, 'noClass');
      }
    });
  }
})();

function featureHeading(){
  // show active heading at top.
  const linkClass = "section_link";
  const titleClass = "section_title";
  const parent = elem(".aside");
  if(parent) {
    let activeHeading = elem(`.${linkClass}.${active}`);
    activeHeading = activeHeading ? activeHeading : elem(`.${titleClass}.${active}`);
    parent.scroll({
      top: activeHeading.offsetTop,
      left: 0,
      // behavior: 'smooth'
    });
  }
}

function activeHeading(position, listLinks) {
  let linksToModify = Object.create(null);
  linksToModify.active = listLinks.filter(function(link) {
    return containsClass(link, active);
  })[0];

  // activeTocLink ? deleteClass

  linksToModify.new = listLinks.filter(function(link){
    return parseInt(link.dataset.position) === position
  })[0];

  if (linksToModify.active != linksToModify.new) {
    linksToModify.active ? deleteClass(linksToModify.active, active): false;
    pushClass(linksToModify.new, active);
  }
};

setTimeout(() => {
  featureHeading();
}, 50);

function loadActions() {
  (function updateDate() {
    const date = new Date();
    const year = date.getFullYear();
    const yearEl = elem('.year');
    yearEl ? year.innerHTML = year : false;
  })();

  (function customizeSidebar(){
    const tocActive = 'toc_active';
    const aside = elem('aside');
    const tocs = elems('nav', aside);
    if(tocs) {
      tocs.forEach(function(toc){
        toc.id = "";
        pushClass(toc, 'toc');
        if(toc.children.length >= 1) {
          const tocItems = Array.from(toc.children[0].children);

          const previousHeading = toc.previousElementSibling;
          previousHeading.matches(`.${active}`) ? pushClass(toc, tocActive) : false;

          tocItems.forEach(function(item){
            pushClass(item, 'toc_item');
            pushClass(item.firstElementChild, 'toc_link');
          });
        }
      });

      const currentToc = elem(`.${tocActive}`);

      if(currentToc) {
        const pageInternalLinks = Array.from(elems('a', currentToc));

        const pageIds = pageInternalLinks.map(function(link){
          return link.hash;
        });

        const linkPositions = pageIds.map(function(id){
          const heading = document.getElementById(decodeURIComponent(id.replace('#','')));
          const position = heading.offsetTop;
          return position;
        });

        pageInternalLinks.forEach(function(link, index){
          link.dataset.position = linkPositions[index]
        });

        window.addEventListener('scroll', function(e) {
          // this.setTimeout(function(){
          let position = window.scrollY;
          let active = closestInt(position, linkPositions);
          activeHeading(active, pageInternalLinks);
          // }, 1500)
        });
      }
    }

    const paragraphs = elems('p');
    if (paragraphs) {
      paragraphs.forEach(function(p){
        const buttons = elems('.button', p);
        if(buttons.length > 1) {
          pushClass(p, 'button_grid');
        }
      });
    }
  })();

  (function markExternalLinks(){
    let links = elems('a');
    if(links) {
      Array.from(links).forEach(function(link){
        let target, rel, blank, noopener, attr1, attr2, url, isExternal;
        url = new URL(link.href);
        // definition of same origin: RFC 6454, section 4 (https://tools.ietf.org/html/rfc6454#section-4)
        isExternal = url.host !== location.host || url.protocol !== location.protocol || url.port !== location.port;
        if(isExternal) {
          target = 'target';
          rel = 'rel';
          blank = '_blank';
          noopener = 'noopener';
          attr1 = elemAttribute(link, target);
          attr2 = elemAttribute(link, noopener);

          attr1 ? false : elemAttribute(link, target, blank);
          attr2 ? false : elemAttribute(link, rel, noopener);
        }
      });
    }
  })();

  let headingNodes = [], results, link, icon, current, id,
  tags = ['h2', 'h3', 'h4', 'h5', 'h6'];

  current = document.URL;

  tags.forEach(function(tag){
    results = document.getElementsByTagName(tag);
    Array.prototype.push.apply(headingNodes, results);
  });

  function sanitizeURL(url) {
    // removes any existing id on url
    const hash = '#';
    const positionOfHash = url.indexOf(hash);
    if(positionOfHash > -1 ) {
      const id = url.substr(positionOfHash, url.length - 1);
      url = url.replace(id, '');
    }
    return url
  }

  headingNodes.forEach(function(node){
    link = createEl('a');
    icon = createEl('img');
    icon.src = '{{ absURL "icons/link.svg" }}';
    link.className = 'link icon';
    link.appendChild(icon);
    id = node.getAttribute('id');
    if(id) {
      link.href = `${sanitizeURL(current)}#${id}`;
      node.appendChild(link);
      pushClass(node, 'link_owner');
    }
  });

  function copyFeedback(parent) {
    const copyText = document.createElement('div');
    const yanked = 'link_yanked';
    copyText.classList.add(yanked);
    copyText.innerText = 'Link Copied';
    if(!elem(`.${yanked}`, parent)) {
      const icon = parent.getElementsByTagName('img')[0];
      const originalSrc = icon.src;
      icon.src = '{{ absURL "icons/check.svg" }}';
      parent.appendChild(copyText);
      setTimeout(function() {
        parent.removeChild(copyText)
        icon.src = originalSrc;
      }, 2250);
    }
  }

  (function copyHeadingLink() {
    let deeplink, deeplinks, newLink, parent, target;
    deeplink = 'link';
    deeplinks = elems(`.${deeplink}`);
    if(deeplinks) {
      document.addEventListener('click', function(event)
      {
        target = event.target;
        parent = target.parentNode;
        if (target && containsClass(target, deeplink) || containsClass(parent, deeplink)) {
          event.preventDefault();
          newLink = target.href != undefined ? target.href : target.parentNode.href;
          copyToClipboard(newLink);
          target.href != undefined ?  copyFeedback(target) : copyFeedback(target.parentNode);
        }
      });
    }
  })();

  const light = 'light';
  const dark = 'dark';
  const storageKey = 'colorMode';
  const key = '--color-mode';
  const data = 'data-mode';
  const bank = window.localStorage;

  function prefersColor(mode){
    return `(prefers-color-scheme: ${mode})`;
  }

  function systemMode() {
    if (window.matchMedia) {
      const prefers = prefersColor(dark);
      return window.matchMedia(prefers).matches ? dark : light;
    }
    return light;
  }

  function currentMode() {
    let acceptableChars = light + dark;
    acceptableChars = [...acceptableChars];
    let mode = getComputedStyle(doc).getPropertyValue(key).replace(/\"/g, '').trim();

    mode = [...mode].filter(function(letter){
      return acceptableChars.includes(letter);
    });

    return mode.join('');
  }

  /**
   * @param isDarkMode true means from dark to light, false means from light to dark
   */
  function changeMode(isDarkMode) {
    if(isDarkMode) {
      bank.setItem(storageKey, light)
      elemAttribute(doc, data, light);
    } else {
      bank.setItem(storageKey, dark);
      elemAttribute(doc, data, dark);
    }
  }

  (function lazy() {
    function lazyLoadMedia(element) {
      let mediaItems = elems(element);
      if(mediaItems) {
        Array.from(mediaItems).forEach(function(item) {
          item.loading = "lazy";
        });
      }
    }
    lazyLoadMedia('iframe');
    lazyLoadMedia('img');
  })();

  (function makeTablesResponsive(){
    const tables = elems('table');
    if (tables) {
      tables.forEach(function(table){
        const tableWrapper = createEl();
        pushClass(tableWrapper, 'scrollable');
        wrapEl(table, tableWrapper);
      });
    }
  })();

  function pickModePicture(user, system, context) {
    const pictures = elems('picture');
    if(pictures) {
      pictures.forEach(function(picture){
        let source = picture.firstElementChild;
        if(user == system) {
          context ? source.media = prefersColor(dark) : false;
        } else {
          if(system == light) {
            source.media = (user === dark) ? prefersColor(light) : prefersColor(dark) ;
          } else {
            source.media = (user === dark) ? prefersColor(dark) : prefersColor(light) ;
          }
        }
      });
    }
  }

  function setUserColorMode(mode = false) {
    const isDarkMode = currentMode() == dark;
    const storedMode = bank.getItem(storageKey);
    const sysMode = systemMode();
    if(storedMode) {
      if(mode) {
        changeMode(isDarkMode);
      } else {
        elemAttribute(doc, data, storedMode);
      }
    } else {
      if(mode === true) {
        changeMode(isDarkMode)
      } else {
        changeMode(sysMode!==dark);
      }
    }
    const userMode = doc.dataset.mode;
    doc.dataset.systemmode = sysMode;
    if(userMode) {
      pickModePicture(userMode,sysMode,mode);
    }
  }

  setUserColorMode();

  doc.addEventListener('click', function(event) {
    let target = event.target;
    let modeClass = 'color_choice';
    let isModeToggle = containsClass(target, modeClass);
    if(isModeToggle) {
      setUserColorMode(true);
    }
    toggleMenu(event);
  });

  (function backToTop(){
    const toTop = elem("#toTop");
    window.addEventListener("scroll", function(e) {
      const lastKnownScrollPosition = window.scrollY;
      if(lastKnownScrollPosition >= 200) {
        toTop.style.display = "flex";
        const viewPort = window.innerWidth;
        const maxBodyWidth = 1240;
        // if(viewPort > maxBodyWidth) {
        //   toTop.style.right = `${((viewPort - maxBodyWidth) / 2)}px`;
        // }
        pushClass(toTop, active);
      } else {
        deleteClass(toTop, active);
      }
    });
  })();

}

window.addEventListener('load', loadActions());
