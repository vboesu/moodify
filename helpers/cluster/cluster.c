#include <stdint.h>
#include <stdio.h>

#include "data.c"

uint64_t max(uint64_t x, uint64_t y) { return x > y ? x : y; }

void array_zero(uint64_t *arr, int n)
{
    for (int i = 0; i < n; i++)
    {
        arr[i] = 0;
    }
}

void array_copy(uint64_t *dest, uint64_t *src, uint32_t n)
{
    for (int i = 0; i < n; i++)
    {
        dest[i] = src[i];
    }
}

void array_add(uint64_t *dest, uint64_t *src, uint32_t n)
{
    for (int i = 0; i < n; i++)
    {
        dest[i] += src[i];
    }
}

void array_divide(uint64_t *arr, uint64_t by, uint32_t n)
{
    // Divide each entry in the array by a number
    if (by == 0)
    {
        return;
    }

    for (int i = 0; i < n; i++)
    {
        arr[i] /= by;
    }
}

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

void assign(uint64_t *points, uint32_t n_points, uint32_t dim, uint64_t *centers, uint64_t n_centers)
{
    // Go through all data points
    for (int i = 0; i < n_points; i++)
    {
        uint64_t min_dist = UINT64_MAX;
        // Compute distances to all centers
        for (int j = 0; j < n_centers; j++)
        {
            uint64_t dist = distance(&points[i * dim], &centers[j * dim], dim - 1);
            // Update if new smallest distance is found
            if (dist < min_dist)
            {
                min_dist = dist;
                // Assign index of center to point
                points[i * dim + dim - 1] = j;
            }
        }
    }
}

uint64_t update(uint64_t *points, uint32_t n_points, uint32_t dim, uint64_t *centers, uint64_t n_centers, uint64_t *tmp)
{
    // Initialize variables to 0
    uint64_t error = 0;
    array_zero(tmp, n_centers * dim);

    // Go through all points
    for (int i = 0; i < n_points; i++)
    {
        uint64_t center = points[(i + 1) * dim - 1];
        
        // Accumulate points in tmp to compute average
        array_add(&tmp[center * dim], &points[i * dim], dim - 1);

        // Keep track of how many points are assigned to each center
        tmp[(center + 1) * dim - 1] += 1;
    }

    for (int i = 0; i < n_centers; i++)
    {
        // Take weighted average based on counts
        array_divide(&tmp[i * dim], tmp[(i + 1) * dim - 1], dim - 1);

        // Compute distance from previous center
        uint64_t dist = distance(&centers[i * dim], &tmp[i * dim], dim - 1);

        // The error is the largest center displacement
        error = max(error, dist);

        // Update centers
        array_copy(&centers[i * dim], &tmp[i * dim], dim - 1);
    }

    return error;
}

void cluster(
    uint64_t *points, uint32_t n_points, uint32_t dim, 
    uint64_t *centers, uint64_t n_centers,
    uint16_t tolerance, int max_iter)
{
    // Keep track of iterations and center displacements
    uint64_t remaining_iter = max(max_iter, 1);
    uint64_t tmp[n_centers * dim];
    uint64_t diff = 0;

    array_zero(tmp, n_centers * dim);

    while (remaining_iter > 0) 
    {
        remaining_iter -= 1;

        assign(points, n_points, dim, centers, n_centers);
        diff = update(points, n_points, dim, centers, n_centers, tmp);

        if (remaining_iter < 1 || diff <= tolerance) 
        {
            return;
        }
    }
}