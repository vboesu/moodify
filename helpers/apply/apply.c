#include <stdint.h>
#include <stdio.h>

int max(int x, int y) { return x > y ? x : y; }
int min(int x, int y) { return x < y ? x : y; }

uint64_t distance(uint64_t *a, uint64_t *b, uint32_t dim)
{
    // Compute squared euclidean distance
    uint64_t sum = 0;
    for (int i = 0; i < dim; i++)
    {
        sum += (b[i] - a[i]) * (b[i] - a[i]);
    }

    return sum;
}

void apply(uint64_t *img, uint64_t *source_rgb, uint64_t *target_rgb, uint64_t n, uint64_t dim, uint64_t n_palette)
{
    // Go through all pixels
    for (int i = 0; i < n; i += dim)
    {
        // Get smallest distance to source_rbg (see assign function in cluster.c)
        uint64_t min_dist = UINT64_MAX;
        uint8_t min_dist_idx = 0;
        for (uint8_t j = 0; j < n_palette * dim; j += dim)
        {
            uint64_t dist = distance(&img[i], &source_rgb[j], dim);
            if (dist < min_dist)
            {
                min_dist = dist;
                min_dist_idx = j;
            }
        }

        // Assign inverse to smallest source_rgb to pixel
        for (uint8_t j = 0; j < dim; j++)
        {
            int new = target_rgb[min_dist_idx + j] - (source_rgb[min_dist_idx + j] - img[i + j]);

            // Clip between [0, 255]
            new = min(255, max(0, new));
            img[i + j] = new;
        }
    }
}