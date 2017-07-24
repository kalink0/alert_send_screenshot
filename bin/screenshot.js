var casper = require('casper').create({ verbose: true, logLevel: 'debug', viewportSize: { width: 1920, height: 600 }, waitTimeout: 10000 });

function removeShadowPath () {
    var nodes = document.querySelectorAll('*[stroke-opacity]');
    for (var i = 0; i < nodes.length; i++) {
        var elem = nodes[i];
        var strokeOpacity = elem.getAttribute('stroke-opacity');
        elem.removeAttribute('stroke-opacity');
        elem.setAttribute('opacity', strokeOpacity);
    }
}


phantom.addCookie({
    'name': 'splunkd_' + casper.cli.get(5),
    'value' : casper.cli.get(3),
    'domain' : casper.cli.get(4),
    'path' : '/'
})


if (casper.cli.has(0)) {
    casper.start(casper.cli.get(0), function () {
        this.page.paperSize = { format: 'A2', orientation: 'portrait', margin: '1cm' }
    });

    if (casper.cli.has(1))
        duration = (+casper.cli.get(1)) * 1000;

    casper.then(function () {
        this.wait(duration, function () {
            this.page.evaluate(removeShadowPath);
            if (casper.cli.get(6) == 'png')
                this.capture(casper.cli.get(2) + '.' + casper.cli.get(6));
            if (casper.cli.get(6) == 'pdf')
                this.capture(casper.cli.get(2) + '.' + casper.cli.get(6), undefined, { type: 'pdf' });
        });
    });
}

casper.run();
