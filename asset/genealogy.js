(() => {
    'use strict';
    const viewLinks = [...document.querySelectorAll('[data-view]')];
    const panels = [...document.querySelectorAll('[data-panel]')];
    const board = document.getElementById('tree-board');
    const tree = document.getElementById('family-tree');
    let treeStarted = false;
    let scale = 1;

    // Keep the entire page readable without JavaScript; enhance the views as tabs.
    document.body.classList.add('genealogy-ready');
    document.querySelector('.view-switch').setAttribute('role', 'tablist');
    viewLinks.forEach(link => {
        link.id = `tab-${link.dataset.view}`;
        link.setAttribute('role', 'tab');
        link.setAttribute('aria-controls', `${link.dataset.view}-view`);
        link.addEventListener('click', event => {
            event.preventDefault();
            activateView(link.dataset.view);
        });
        link.addEventListener('keydown', event => {
            if (event.key === ' ') {
                event.preventDefault();
                activateView(link.dataset.view);
                return;
            }
            const index = viewLinks.indexOf(link);
            let next;
            if (event.key === 'ArrowRight') next = (index + 1) % viewLinks.length;
            if (event.key === 'ArrowLeft') next = (index + viewLinks.length - 1) % viewLinks.length;
            if (event.key === 'Home') next = 0;
            if (event.key === 'End') next = viewLinks.length - 1;
            if (next !== undefined) {
                event.preventDefault();
                activateView(viewLinks[next].dataset.view);
                viewLinks[next].focus();
            }
        });
    });
    panels.forEach(panel => {
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('aria-labelledby', `tab-${panel.dataset.panel}`);
        panel.tabIndex = 0;
    });

    function activateView(view) {
        viewLinks.forEach(link => {
            const selected = link.dataset.view === view;
            link.classList.toggle('is-active', selected);
            link.setAttribute('aria-selected', String(selected));
            link.tabIndex = selected ? 0 : -1;
        });
        panels.forEach(panel => { panel.hidden = panel.dataset.panel !== view; });
        if (view === 'tree' && !treeStarted) {
            treeStarted = true;
            requestAnimationFrame(() => {
                setScale(scale, false);
                // Start at the earliest row with the cards at a readable size.
                const people = [...tree.querySelectorAll('.tree-person')].map(person => ({
                    x: Number(person.dataset.x),
                    y: Number(person.dataset.y)
                }));
                const firstY = Math.min(...people.map(person => person.y));
                const firstRow = people.filter(person => person.y === firstY);
                const firstX = firstRow.reduce((sum, person) => sum + person.x, 0) / firstRow.length;
                board.scrollLeft = (firstX - tree.viewBox.baseVal.x) * scale - board.clientWidth / 2;
                board.scrollTop = 0;
            });
        }
    }
    activateView('tree');

    // Native scroll keeps mouse, touch and keyboard exploration consistent.
    function setScale(next, keepCenter = true) {
        const old = scale;
        const bounds = tree.viewBox.baseVal;
        const oldInset = Math.max(0, (board.clientWidth - bounds.width * old) / 2);
        const centerX = (board.scrollLeft + board.clientWidth / 2 - oldInset) / old;
        const centerY = (board.scrollTop + board.clientHeight / 2) / old;
        scale = Math.min(1.6, Math.max(0.1, next));
        tree.style.width = `${bounds.width * scale}px`;
        tree.style.height = `${bounds.height * scale}px`;
        const output = document.getElementById('tree-zoom');
        output.value = `${Math.round(scale * 100)}%`;
        output.textContent = output.value;
        document.querySelector('[data-zoom="out"]').disabled = scale <= 0.1;
        document.querySelector('[data-zoom="in"]').disabled = scale >= 1.6;
        if (keepCenter) {
            const newInset = Math.max(0, (board.clientWidth - bounds.width * scale) / 2);
            board.scrollLeft = centerX * scale + newInset - board.clientWidth / 2;
            board.scrollTop = centerY * scale - board.clientHeight / 2;
        }
    }
    document.querySelectorAll('[data-zoom]').forEach(button => {
        button.addEventListener('click', () => setScale(scale + (button.dataset.zoom === 'in' ? 0.15 : -0.15)));
    });
    document.getElementById('tree-fit').addEventListener('click', () => setScale((board.clientWidth - 12) / tree.viewBox.baseVal.width));
    const fullscreen = document.getElementById('tree-fullscreen');
    const viewer = document.getElementById('tree-viewer');
    if (!viewer.requestFullscreen) fullscreen.hidden = true;
    else fullscreen.addEventListener('click', async () => {
        try {
            if (document.fullscreenElement) await document.exitFullscreen();
            else await viewer.requestFullscreen();
        } catch (_) {
            // Scrolling and zoom remain available if the browser denies fullscreen.
        }
    });
    document.addEventListener('fullscreenchange', () => {
        fullscreen.setAttribute('aria-label', document.fullscreenElement ? 'Exit full screen' : 'View tree in full screen');
        fullscreen.firstChild.textContent = document.fullscreenElement ? 'Close ' : 'Expand ';
    });

})();
