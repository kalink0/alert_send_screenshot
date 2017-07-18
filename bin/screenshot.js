// modify the login credential here


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



console.log("The session key: " + casper.cli.get(3));

phantom.addCookie({
    'name': 'splunkd_8000',
    'value' : casper.cli.get(3),
    'domain' : 'ubuntu-server',
    'path' : '/'
})


if (casper.cli.has(0)) {
    casper.start(casper.cli.get(0), function () {
        this.page.paperSize = { format: 'A2', orientation: 'portrait', margin: '1cm' }
        //casper.waitForSelector('form.loginForm', function () {
        //    this.fill('form', { username: username, password: password }, true);
        //});
    });

    var duration = 30000;
    if (casper.cli.has(1))
        duration = (+casper.cli.get(1)) * 1000;

    casper.then(function () {
        this.wait(duration, function () {
            this.page.evaluate(removeShadowPath);
            this.capture(casper.cli.has(2) ? casper.cli.get(2) + '.pdf' : 'report.pdf', undefined, { type: 'pdf' });
            this.capture(casper.cli.has(2) ? casper.cli.get(2) + '.png' : 'report.png');
        });
    });
}

casper.run();
