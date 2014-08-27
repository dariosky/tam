module.exports = function (grunt) {
	// Configure grunt
	grunt.initConfig({
		sprite: {
			all: {
				src: 'tam/static/sprites/*.png',
				destImg: 'tam/static/tam_sprites.png',
				destCSS: 'tam/static/tam_sprites.css',
				algorithm: 'binary-tree'
			}
		}
	});

	// Load in `grunt-spritesmith`
	grunt.loadNpmTasks('grunt-spritesmith');
};
