var Code = {};

/**
 * Blockly's main workspace.
 * @type {Blockly.WorkspaceSvg}
 */
Code.workspace = null;

Code.loadBlocks = function (defaultXml) {
    try {
        var loadOnce = window.sessionStorage.loadOnceBlocks;
    } catch (e) {
        // Firefox sometimes throws a SecurityError when accessing sessionStorage.
        // Restarting Firefox fixes this, so it looks like a bug.
        var loadOnce = null;
    }
    if ('BlocklyStorage' in window && window.location.hash.length > 1) {
        // An href with #key trigers an AJAX call to retrieve saved blocks.
        BlocklyStorage.retrieveXml(window.location.hash.substring(1));
    } else if (loadOnce) {
        // Language switching stores the blocks during the reload.
        delete window.sessionStorage.loadOnceBlocks;
        var xml = Blockly.Xml.textToDom(loadOnce);
        Blockly.Xml.domToWorkspace(xml, Code.workspace);
    } else if (defaultXml) {
        // Load the editor with default starting blocks.
        var xml = Blockly.Xml.textToDom(defaultXml);
        Blockly.Xml.domToWorkspace(xml, Code.workspace);
    } else if ('BlocklyStorage' in window) {
        // Restore saved blocks in a separate thread so that subsequent
        // initialization is not affected from a failed load.
        window.setTimeout(BlocklyStorage.restoreBlocks, 0);
    }
};

Code.bindClick = function (el, func) {
    if (typeof el == 'string') {
        el = document.getElementById(el);
    }
    el.addEventListener('click', func, true);
    el.addEventListener('touchend', func, true);
};

Code.getBBox_ = function (element) {
    var height = element.offsetHeight;
    var width = element.offsetWidth;
    var x = 0;
    var y = 0;
    do {
        x += element.offsetLeft;
        y += element.offsetTop;
        element = element.offsetParent;
    } while (element);
    return {
        height: height,
        width: width,
        x: x,
        y: y
    };
};

Code.TABS_ = ['blocks', 'python', 'xml'];
Code.TABS_DISPLAY_ = [
    'Blocks', 'Python', 'XML',
];

Code.selected = 'blocks';

Code.tabClick = function (clickedName) {
    // If the XML tab was open, save and render the content.
    if (document.getElementById('tab_xml').classList.contains('tabon')) {
        var xmlTextarea = document.getElementById('content_xml');
        var xmlText = xmlTextarea.value;
        var xmlDom = null;
        try {
            xmlDom = Blockly.Xml.textToDom(xmlText);
        } catch (e) {
            var badXml = "XML のエラーです:\n%1\n\nXML の変更をやめるには「OK」、編集を続けるには「キャンセル」を選んでください。"
            var q =
                window.confirm(badXml.replace('%1', e));
            if (!q) {
                // Leave the user on the XML tab.
                return;
            }
        }
        if (xmlDom) {
            Code.workspace.clear();
            Blockly.Xml.domToWorkspace(xmlDom, Code.workspace);
        }
    }

    // Deselect all tabs and hide all panes.
    for (var i = 0; i < Code.TABS_.length; i++) {
        var name = Code.TABS_[i];
        var tab = document.getElementById('tab_' + name);
        tab.classList.add('taboff');
        tab.classList.remove('tabon');
        document.getElementById('content_' + name).style.visibility = 'hidden';
    }

    // Select the active tab.
    Code.selected = clickedName;
    var selectedTab = document.getElementById('tab_' + clickedName);
    selectedTab.classList.remove('taboff');
    selectedTab.classList.add('tabon');
    // Show the selected pane.
    document.getElementById('content_' + clickedName).style.visibility =
        'visible';
    Code.renderContent();

    Blockly.svgResize(Code.workspace);
};

Code.renderContent = function () {
    var content = document.getElementById('content_' + Code.selected);
    // Initialize the pane.
    if (content.id == 'content_xml') {
        var xmlTextarea = document.getElementById('content_xml');
        var xmlDom = Blockly.Xml.workspaceToDom(Code.workspace);
        var xmlText = Blockly.Xml.domToPrettyText(xmlDom);
        xmlTextarea.value = xmlText;
        xmlTextarea.focus();
    } else if (content.id == 'content_python') {
        Code.attemptCodeGeneration(Blockly.Python);
    }
};

/**
 * Attempt to generate the code and display it in the UI, pretty printed.
 * @param generator {!Blockly.Generator} The generator to use.
 */
Code.attemptCodeGeneration = function (generator) {
    var content = document.getElementById('content_' + Code.selected);
    content.textContent = '';
    if (Code.checkAllGeneratorFunctionsDefined(generator)) {
        var code = generator.workspaceToCode(Code.workspace);
        content.textContent = code;
    }
};

/**
 * Check whether all blocks in use have generator functions.
 * @param generator {!Blockly.Generator} The generator to use.
 */
Code.checkAllGeneratorFunctionsDefined = function (generator) {
    var blocks = Code.workspace.getAllBlocks(false);
    var missingBlockGenerators = [];
    for (var i = 0; i < blocks.length; i++) {
        var blockType = blocks[i].type;
        if (!generator[blockType]) {
            if (missingBlockGenerators.indexOf(blockType) == -1) {
                missingBlockGenerators.push(blockType);
            }
        }
    }

    var valid = missingBlockGenerators.length == 0;
    if (!valid) {
        var msg = 'The generator code for the following blocks not specified for ' +
            generator.name_ + ':\n - ' + missingBlockGenerators.join('\n - ');
        Blockly.alert(msg);  // Assuming synchronous. No callback.
    }
    return valid;
};

Code.init = function () {
    var container = document.getElementById('content_area');
    var onresize = function (e) {
        var bBox = Code.getBBox_(container);
        for (var i = 0; i < Code.TABS_.length; i++) {
            var el = document.getElementById('content_' + Code.TABS_[i]);
            el.style.top = bBox.y + 'px';
            el.style.left = bBox.x + 'px';
            // Height and width need to be set, read back, then set again to
            // compensate for scrollbars.
            el.style.height = bBox.height + 'px';
            el.style.height = (2 * bBox.height - el.offsetHeight) + 'px';
            el.style.width = bBox.width + 'px';
            el.style.width = (2 * bBox.width - el.offsetWidth) + 'px';
        }
        // Make the 'Blocks' tab line up with the toolbox.
        if (Code.workspace && Code.workspace.getToolbox().width) {
            document.getElementById('tab_blocks').style.minWidth =
                (Code.workspace.getToolbox().width - 38) + 'px';
            // Account for the 19 pixel margin and on each side.
        }
    };
    window.addEventListener('resize', onresize, false);

    var toolbox = document.getElementById("toolbox");
    var options = {
        toolbox: toolbox,
        // scrollbars: true,
        grid:
        {
            spacing: 25,
            length: 3,
            colour: '#ccc',
            snap: true
        },
        media: '../Blockly/media/',
        zoom:
        {
            controls: true,
            wheel: true
        }
    };
    Code.workspace = Blockly.inject('content_blocks', options);

    Code.loadBlocks('');

    Code.tabClick(Code.selected);

    Code.bindClick('trashButton',
        function () { Code.discard(); Code.renderContent(); });

    for (var i = 0; i < Code.TABS_.length; i++) {
        var name = Code.TABS_[i];
        Code.bindClick('tab_' + name,
            function (name_) { return function () { Code.tabClick(name_); }; }(name));
    }
    onresize();
    Blockly.svgResize(Code.workspace);
}

/**
 * Discard all blocks from the workspace.
 */
Code.discard = function () {
    var count = Code.workspace.getAllBlocks(false).length;
    if (count < 2 ||
        window.confirm(Blockly.Msg['DELETE_ALL_BLOCKS'].replace('%1', count))) {
        Code.workspace.clear();
        if (window.location.hash) {
            window.location.hash = '';
        }
    }
};

Promise.all(
    ["toolbox.xml"].map(async file => {
        return fetch(file).then(
            (res) => {
                return res.text();
            }
        );
    })
).then((xmls) => {
    xmls.forEach((xml) => {
        var parser = new DOMParser();
        var doc = parser.parseFromString(xml, "application/xml");
        document.body.appendChild(doc.documentElement);
    });
}).then(() => {
    Code.init();
});