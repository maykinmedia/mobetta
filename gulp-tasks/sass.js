'use strict';
var gulp = require('gulp');
var sass = require('gulp-sass');
var bourbon = require('bourbon');
var neat = require('bourbon-neat');
var autoprefixer = require('gulp-autoprefixer');
var paths = require('../paths');


/**
 * Sass task
 * Run using "gulp sass"
 * Searches for sass files in paths.sassSrc
 * Compiles sass to css
 * Includes bourbon neat
 * Auto prefixes css
 * Writes css to paths.cssDir
 */
gulp.task('sass', function() {
    // Searches for sass files in paths.sassSrc
    gulp.src(paths.sassSrc)
        // Compiles sass to css
        .pipe(sass({
            outputStyle: 'minified',

            // Includes bourbon neat
            includePaths: bourbon.includePaths.concat(neat.includePaths)
        })
        .on('error', sass.logError))

        // Auto prefixes css
        .pipe(autoprefixer({
            browsers: ['last 2 versions'],
            cascade: false
        }))

        // Writes css to paths.cssDir
        .pipe(gulp.dest(paths.cssDir));
});
