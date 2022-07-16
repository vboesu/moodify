# moodify
Generate color palettes randomly or from an image and apply them in a search or to an image.

## Table of Contents
* [Introduction](#introduction)
* [The Website](#the-website)
* [The Palette Generator](#the-palette-generator)
* [Creating a Palette from an Image](#creating-a-palette-from-an-image)
* [Searching for Images Based on Palette](#searching-for-images-based-on-palette)
* [Applying a Palette to an Image](#applying-a-palette-to-an-image)
* [Various Backend Things](#various-backend-things)
* [Final Notes](#final-notes)

## Introduction
The inspiration for this project came from my own experiences as a web and graphic designer where I had to come up with visually pleasing color palettes for the projects I was working on. I found the website [coolors.co](https://coolors.co) which has been a great help for me but I wanted to expand it by some interesting features. A conversation with my classmate gave me the idea for **Mood Search**, the ability to filter the results of an image search based on how closely it matches the input color palette. Sometimes, though, I had already found a nice image that I wanted to adjust to the color scheme of the project. Filters and Photoshop go a long way but it is still a lot of work and requires skill and time to execute. Therefore, the idea of applying color palettes to images was born.

## The Website
The website is comprised of a frontend and a backend. Both are served to the user using flask, a Python framework for websites we were introduced to during CS 50. The requests for the frontend are handled by ```app.py```, whereas most of the backend is handled in ```api.py```, listening at ```/api```. Separating front- and backend not only into separate files but also separate URLs made it easier to keep track of everything and cleaner to work with.

For the visual design of the website, I drew on previous projects of mine including the Homepage that was part of P-Set 8. Using a layout that relies on flex boxes allows for a modern and responsive web design which I am a big fan of.

To make the website feel even more modern and responsive, I wanted to use AJAX requests for most of the interaction with the server, specifically for generating palettes (it feels much more instantaneous than refreshing the page each time), performing a mood search and applying a palette to an image.

## The Palette Generator
Since the generation of color palettes is at the heart of the website, this is the part that I started with. I implemented the random palette generator in Python since it is not computationally expensive, I am most familiar with it and I could make use of Python classes and interfaces.

I did some research on what kinds of color palettes there are and figured out that I can abstract many of them into what I call "Shift Palettes," i.e. palettes that start with a given color and then shift the hue *n* times to create a color palette (e.g. complementary or triadic color palettes). To allow for any number of colors in the palette (even though I ended up restricting the number to 5 by default), I also implemented a ```fill``` function that creates shades of the existing colors.

A fun thing about colors is that you can name them. Since RGB uses 16.7 million (my generator technically uses less than 3.6 million) colors but no one wants to name all of those colors, I decided to use the color names that Pantone uses, somewhat of an industry standard for color names. For a given color, I compute the 3-D distance to each color names based on its RGB values and return the one that is closest.

## Creating a Palette from an Image
I will be completely honest, writing the clustering algorithm in C took way longer than I had anticipated. On the bright side, I learned a lot about the language and common mistakes as well as how to connect a C library to Python. My motivation for implementing Stephen Lloyd's *k*-means clustering algorithm in C was simple: It was just that much faster than any other implementation in Python. I knew that for the Mood Search, I would have to extract the color palette of hundreds of images and this would be painfully slow if I did it all in Python.

I took inspiration from a project I found on github called [kmeans](https://github.com/numberoverzero/kmeans) by the user numberoverzero. Their implementation was helpful but I didn't like that I had to work with separate objects, and I believed that I could make mine even faster while still sticking to the naive *k*-means clustering method (I was right!)

The concept of Lloyd's algorithm is pretty simple: Starting with random data points as cluster centers, it assigns all points to the closest center, computes the average of all points assigned to a center and uses that average as cluster center for the next iteration. Even though there are obviously limitations to the algorithm, its simplicity, efficiency, and average accuracy explain why it is still the most popular clustering algorithm decades later.

Numpy was very helpful in this since it can access C pointers directly, making the conversion between Python and C arrays much faster and easier.

## Searching for Images Based on Palette
The **Mood Search** uses Pixabay's API to get images related to the input query. I have used Pixabay in the past and it is perfectly suited for this project since the images and its API are not only free but also royalty-free so I did not have to worry about potential copyright issues or restricted APIs.

I decided to make the search asynchronous and multithreaded because this allowed me to both make it as fast as possible and give the user a nicer experience with a progress bar that reflects the status of the search. I use previews of the images instead of the original sizes because they make the process a lot faster while generally achieving similarly accurate results.

The ranking of the images is based on the euclidean distance between the image's and the input palette. This is due to its ease to compute using numpy and because it is generally a good indicator of how closely related two vectors (in this case, color palettes) are. There is an argument to be made to look at the dominant colors within a color palette or to weight very close colors more than outliers but I did not have the time to implement and evaluate these options. My implementation generally achieves fast and acceptable results.

## Applying a Palette to an Image
This was the last part of the project that I started and the one I was most unsure about. The concept is as follows:
1. Extract the color palette from the image (sorted by lightness, "source").
2. Map each color in the source to the corresponding one in the selected color palette ("target") according to its lightness, i.e. the darkest color in source to the darkest color in target etc.
3. For every pixel in the image, compute the difference between the RGB vector of the pixel and the closest color in source ("difference").
4. Apply the inverse of the difference to the color in target that the closest color in source maps to.

I first implemented this in Python because it only takes around ten lines. However, especially for larger images, this was _painfully_ slow. Since the concept of finding the closest center is similar to the assignment step in Lloyd's algorithm, I decided to switch to C and implement the application there. The result: more than 100 times faster than a naive Python implementation and more than 10 times faster than scikit-learn's KMeans.

Admittedly, the function gives mixed results. Sometimes, it looks like a filter was applied to the image (especially when the color palettes are similar in lightness) and other times, it looks a little crazy. For obvious reasons, graphics or images with few colors tend to work significantly better than images with a lot of different colors. Gradients are often messed up because the switch to another color as the closest one happens abruptly from one shade to the other. A possible remedy would be to apply the function outlined in steps 3 and 4 above not just on the closest color but on all colors in the palette, weighted by the inverse of the difference but this goes way beyond the scope of this project. It was meant more as a fun proof of concept than a revolutionary breakthrough in image editing technology.

## Various Backend Things
To manage the database, I used a simple ORM wrapper called ```peewee```. It automatically creates the tables, converts the rows to Python objects, and protects from injection attacks.

For the purpose of this project, I felt like validating files based on their extension rather than checking if the file was actually of the format was sufficient.

Searches and images downloaded from Pixabay are cached so that a change of the palette or a refresh of the page only takes a fraction of the time compared to a new search.

## Final Notes
There are certainly a lot of other design decisions I made that could be justified at this point. I tried to follow best practices that I learned in the industry and attempted to make the project both extendible, broad in scope and functional on all browsers. I hope I answered most of the questions about my implementation but if any still remain, do feel free to ask me about them.

