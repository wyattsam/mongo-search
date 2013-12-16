#!/usr/bin/env phantomjs
var baseUrl = 'https://groups.google.com/forum/';
var forumUrl = baseUrl + '#!forum/';
var groupUrl = forumUrl + 'mongodb-user';
var jquery = 'https://ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js';

var page = require('webpage').create();

page.viewportSize = { width: 1600, height: 1000 };
page.settings.loadImages = false;
page.settings.webSecurityEnabled = false;

page.onResourceError = function(resourceError) {
    console.log('Unable to load resource (URL:' + resourceError.url + ')');
    console.log('Error code: ' + resourceError.errorCode + '. Description: ' + resourceError.errorString);
};

page.onResourceRequested = function(request) {
    //console.log('request' + JSON.stringify(request, undefined, 4) );
};

page.onConsoleMessage = function (msg) {
    //console.log(msg);
};

var processThreads = function() {
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
    var topics = page.evaluate(processThreads);
    var json = JSON.stringify(topics);
    postData(json);
    page.evaluate(scrollDown);
    setTimeout(grabPage, 1000);
};

var postData = function(json) {
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "POST", 'http://localhost:5000/phantom', true );
    xmlHttp.setRequestHeader('Content-type','application/json;');
    xmlHttp.setRequestHeader("Content-length", json.length);
    xmlHttp.setRequestHeader("Connection", "close");

    xmlHttp.onreadystatechange = function(){
        if (xmlHttp.readyState != 4) return;
        if (xmlHttp.status != 200 && xmlHttp.status != 304) {
            return 'error';
        };
        return 'success';
    };

    xmlHttp.send(json);
};

page.open(groupUrl, function(worked) {
    console.log('[status] opening page');
    if (worked !== 'success') {
        console.log('[status] problem opening page');
    } else {
        page.includeJs(jquery, function() {
            grabPage();
        });
    };
});
