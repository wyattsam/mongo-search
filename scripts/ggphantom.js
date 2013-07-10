var baseUrl = 'https://groups.google.com/forum/';
var forumUrl = baseUrl + '#!forum/';
var groupUrl = forumUrl + 'mongodb-user';
var jquery = 'https://ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js';

var page = require('webpage').create();

page.viewportSize = { width: 1600, height: 1000 };

page.onResourceRequested = function(request) {
    //console.log('request' + JSON.stringify(request, undefined, 4) );
};

page.onConsoleMessage = function (msg) {
    //console.log(msg);
};

var processThread = function() {
    var topics = [];
    var selection = $('table[role=list] tr > td > div a:visible:not(.visited)');
    selection.each(function(index, elem){
        var sel = $(elem);
        // mark element as visited
        sel.addClass('visited')
        var subject = sel.text();
        var href = sel.attr('href');
        topics.push({ 'subject': subject, 'href': href });
    });
    return topics;
};

var scrollDown = function(){
    var $scrollBox = $("div[role=main] > div > div > div > div > div").last();
    $scrollBox.scrollTop($scrollBox.scrollTop() + 3600);
};

var grabPage = function() {
    var topics = page.evaluate(processThread);
    topics.map(function(topic) {
        console.log(topic.subject + " ---> " + baseUrl + topic.href);
    });
    page.evaluate(scrollDown);
    setTimeout(grabPage, 3000);
};

page.open(groupUrl, function(worked) {
    console.log('opening page');
    if (worked !== 'success') {
        console.log('problem opening page');
    } else {
        page.includeJs(jquery, function() {
            grabPage();
        });
    };
});
