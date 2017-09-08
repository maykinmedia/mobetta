var path = require('path');
var fs = require('fs');


/** Parses package.json */
var pkg = JSON.parse(fs.readFileSync('./package.json', 'utf-8'));

/** Name of the sources directory */
var sourcesRoot = './mobetta/static/mobetta/';


/**
 * Application path configuration for use in frontend scripts
 */
module.exports = {
    // Parsed package.json
    package: pkg,

    // Path to the sass (sources) directory
    sassSrc: sourcesRoot + 'sass/**/*.scss',

    // Path to the (compiled) css directory
    cssDir: sourcesRoot + 'css/',
};
