---
title: The Derangement of Secret Santa
date: 2025-12-26 20:00:00 +0200
categories:
  - side-quest
tags:
  - family
  - mathematics
  - simulation
math: true
---

In our family, we have the tradition of doing a Secret Santa for Christmas. Even though there are tools to draw names digitally, we prefer to do it the old-fashioned way by putting a piece of paper for each name in a cup. This way, there is no control over who draws which name, except that you have to put the drawn name back if you draw yourself. Surprisingly, most years we drew in a perfect circle, meaning the first person to give is the last person to get. As it happened again this year, I wondered: what are the odds of drawing in a perfect circle?

In this blog post, I tackle this problem in two ways: [analytically](#getting-combinatorial-mathematics-involved), using combinatorics, and [experimentally](#simulating-millions-of-draws), by running a simulation. But before we can get to that, we have to find a more [general version of the problem](#abstracting-the-problem) by defining what a "perfect draw" actually is. If you are just here for the results, you can [jump straight to them](#findings).

> Curious about the odds for your party? Calculate them quickly with the [tool](#compute-the-odds-yourself) at the bottom of this page!
{: .prompt-tip }

## Abstracting the Problem

We can represent each person $p_i$ in our company of $n$ people as an element in a list: $[p_0, p_1, \dots p_{n-1}]$. The order of the elements in this list is not important, as long as we assume a fixed order for the original list of persons. Each shuffle, or permutation, of this list represents a possible draw of names. Namely, the person ending up at position 0 is the person $p_0$ drew, the person ending up at position 1 is the person $p_1$ drew, and so forth. 

Let's look at an example with four people. Our original list is $[p_0, p_1, p_2, p_3]$. A possible permutation of this list is $[p_1, p_3, p_2, p_0]$, with the following draws:
- Person 0 drew the name of person 1 ($p_1$ is at index 0 in the shuffled list).
- Person 1 drew the name of person 3 ($p_3$ is at index 1 in the shuffled list).
- Person 2 drew its own name ($p_2$ is at index 2 in the shuffled list).
- Person 3 drew the name of person 0 ($p_0$ is at index 3 in the shuffled list).

This example shows that if any person appears in their original index, in other words, if any person does not change position from the original list, the draw is invalid because at least one person has drawn their own name.

On the other hand, we have a perfect draw if, when we follow the chain of draws, we encounter every person before returning to the person we started with. For example, for the shuffle $[p_1, p_3, p_0, p_2]$, we can follow the draws starting with the first person: $p_0 \rightarrow p_1 \rightarrow p_3 \rightarrow p_2 \rightarrow p_0$. In this case, we encounter every person, and the last one is the same as the one we started with. This check is independent of the chosen starting person. We can say that, for a perfect draw, the chain of draws must form a single circle. As soon as we can form multiple circles, or if any person is missing from the circle, we no longer have a perfect draw.


## Getting Combinatorial Mathematics Involved

We've generalized the problem to the permutations of a list of $n$ unique elements, where each element refers to its starting position. Now let's try to find expressions for the total number of possible draws, the number of possible valid draws, and the number of possible perfect draws.

### Total Number of Permutations
The total number of permutations of a list of length $n$ is the [factorial](https://en.wikipedia.org/wiki/Factorial) of $n$, denoted as $n!$. We can place the first element in $n$ positions, the second element in any of the remaining $n-1$ possible positions, the third has $n-2$ possible positions left, and so on. Multiplying this gives the total number of possible permutations: $n(n-1)(n-2)\dots1=n!$. 

### Number of Possible Perfect Draws
We can derive the number of possible permutations that represent a perfect draw in a similar way. In this case, the first element, $p_0$, has only $n - 1$ possible positions because it cannot remain in its original position. For the second element, $p_1$, we have two possible scenarios:
- $p_0$ is not placed at index 1. In this case, one position other than position 1 is already taken, and $p_1$ cannot take position 1 (because then it would draw itself, resulting in an invalid draw), so there are $n - 2$ possible positions.
- $p_0$ is placed at index 1. In this case, $p_1$ cannot take position 0 because then we would close the circle with $p_0 \rightarrow p_1$ and $p_1 \rightarrow p_0$, so there are again $n - 2$ possible positions (as $p_1$ can also not take position 1 for the same reason as in the first scenario).

We can repeat this reasoning for every element, which makes the last element point to the first element. Thus, in this case there are $(n - 1)(n - 2) \dots 1 = (n - 1)!$ possible permutations that represent a perfect circle.

### Number of Valid Draws
Finding an expression for the number of possible valid draws is a bit harder. This is the number of permutations where all elements leave their original position. Luckily my girlfriend enlightened me with the existence of [derangements](https://en.wikipedia.org/wiki/Derangement) which is exactly what we need:
> In [combinatorial](https://en.wikipedia.org/wiki/Combinatorics "Combinatorics") [mathematics](https://en.wikipedia.org/wiki/Mathematics "Mathematics"), a **derangement** is a [permutation](https://en.wikipedia.org/wiki/Permutation "Permutation") of the elements of a [set](https://en.wikipedia.org/wiki/Set_\(mathematics\) "Set (mathematics)") in which no element appears in its original position. In other words, a derangement is a permutation that has no [fixed points](https://en.wikipedia.org/wiki/Fixed_point_\(mathematics\) "Fixed point (mathematics)").
>
>The number of derangements of a set of size n is known as the **subfactorial** of n or the n th **derangement number** or n th **de Montmort number** (after [Pierre Remond de Montmort](https://en.wikipedia.org/wiki/Pierre_Remond_de_Montmort "Pierre Remond de Montmort")).

We can compute the number of derangements, denoted as $!n$, in two ways:

- $$
!n = (n-1)\left(!(n-1) + !(n-2) \right)
$$
for $n\geq2$, where $!0=1$ and $!1=0$.

- $$
!n = \left[ \frac{n!}{e} \right] = \left\lfloor \frac{n!}{e} + \frac12 \right\rfloor = \left\lfloor \frac{n!+1}{e} \right\rfloor
$$
for $n\geq1$.

### Probabilities
We can use the previous findings to define the following probabilities:
- Probability of a valid draw: $P_{\mathrm{valid \ draw}} = \frac{!n}{n!}$
- Probability of a perfect draw: $P_{\mathrm{perfect \ draw}} = \frac{(n-1)!}{n!}$
- Probability of a perfect draw given that only valid draws are allowed: $P_{\mathrm{perfect \ draw \vert valid \ draw}} = \frac{(n-1)!}{!n}$

Note that, apart from the nonlinear rounding element, the probability of a valid draw is essentially constant.

## Simulating Millions of Draws

My first approach to this problem was to write a program that could simulate millions of draws and report the number of valid and perfect draws. I like to see things confirmed by experimental results, and for these kinds of problems, running a simulation is the most straightforward way of doing so. Because I only need to perform operations on a fixed-length array of integers, I could use C to write the simulation program and benefit from its more efficient execution compared to languages like Python. Besides that, it was a great excuse to refresh my C knowledge.

I'll use the same concept of a list of people, where each person is represented by an integer equal to its starting index. A simulation for $n$ people starts by building an original `names` array: $[0, 1, 2, \dots, n-1]$. Each iteration then copies `names` into a `draws` array and shuffles `draws`. This allows us to manipulate `draws` freely while keeping the original `names` array intact for the next iteration, without needing to rebuild it. The iteration ends by checking whether the random draw is valid or perfect and updating the corresponding counters. Below is the code fragment that runs a simulation for a list of `N` people with `NB_SIMS` iterations.
```c
// Build [0, 1, ...N-1] array representing the names
int *names = malloc(N * sizeof(int));
for (size_t i = 0; i < N; ++i) names[i] = (int)i;

// Variables to keep stats
int nb_sims = 0;
int nb_invalid = 0;
int nb_perfect = 0;

// Run simulation
int *draws = malloc(N * sizeof(int));
while (nb_sims < NB_SIMS) {
	// Copy the names array
	memcpy(draws, names, N * sizeof(int));
	
	// Shuffle the draws
	shuffle(draws, N);
	
	// Check the draw
	if (!valid_draw(draws, N)) {
		nb_invalid++;
	} else if (perfect_circle(draws, N)) {
		nb_perfect++;
	}
	nb_sims++;
}

free(names);
free(draws);
```

That leaves us with the problem of checking whether a shuffled `draws` array represents a valid or a perfect draw. Let's start with a valid draw. A draw is valid when every element has moved from its original position. Because our elements are their starting indexes, we can loop over the array and check whether any element equals its index. If so, the draw is invalid. Here is a function that does just that.
```c
bool valid_draw(int *draws, size_t N) {
    for (size_t i = 0; i < N; i++) {
        if (draws[i] == i) return false;
    }
    return true;
}
```

Checking whether a draw is perfect is a bit harder. I ended up with a code that starts with the first element and follows the chain of draws. It looks at the value `j` of `draws[0]`, then at the value of `draws[j]`, and so on. The function marks each index it has already checked by setting its value to `-1`. This way, the function knows it has completed the chain of draws when it encounters a `-1` value. If we then record the length of the followed chain, we can compare it with the length of the `draws` array. Only if they are equal do we have a perfect draw. Here is that logic written as a C function.
```c
bool perfect_circle(int *draws, size_t N) {
    size_t i = 0;
    size_t n = 0;
    while (draws[i] != -1) {
        size_t j = draws[i];
        draws[i] = -1;
        i = j;
        n++;
    }
    return n == N;
}
```

If we combine everything, including a function to shuffle an array, we obtain the C file shown below. In this file, I added simulation constants, safety checks for null-pointers, and code to print and save the simulation results to a CSV file. Because simulations for different `N` values are independent, I also implemented multithreading to run multiple simulations simultaneously. This, of course, required adding a lock when writing the results. 
```c
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdbool.h>
#include <string.h>
#include <pthread.h>

#define NB_SIMS 10000000
#define MAX_N 100
#define NB_THREADS 10
#define DISCARD_INVALID true

FILE *fptr;
pthread_mutex_t write_mutex = PTHREAD_MUTEX_INITIALIZER;

// Source - https://benpfaff.org/writings/clc/shuffle.html
void shuffle(int *array, size_t n) {
    if (n > 1) {
        size_t i;
        for (i = 0; i < n - 1; i++) {
          size_t j = i + rand() / (RAND_MAX / (n - i) + 1);
          int t = array[j];
          array[j] = array[i];
          array[i] = t;
        }
    }
}

bool valid_draw(int *draws, size_t N) {
    if (N > 0 && draws == NULL) return false;
    for (size_t i = 0; i < N; i++) {
        if (draws[i] == i) return false;
    }
    return true;
}

bool perfect_circle(int *draws, size_t N) {
    if (N > 0 && draws == NULL) return false;
    size_t i = 0;
    size_t n = 0;
    while (draws[i] != -1) {
        size_t j = draws[i];
        draws[i] = -1;
        i = j;
        n++;
    }
    return n == N;
}

void simulate(size_t N) {
    // Build [0, 1, ...N-1] array representing the names
    int *names = malloc(N * sizeof(int));
    for (size_t i = 0; i < N; ++i) names[i] = (int)i;

    // Variables to keep stats
    int nb_sims = 0;
    int nb_invalid = 0;
    int nb_perfect = 0;

    // Run simulation
    int *draws = malloc(N * sizeof(int));
    while (nb_sims < NB_SIMS) {
        // Copy the names array
        memcpy(draws, names, N * sizeof(int));
        
        // Shuffle the draws
        shuffle(draws, N);
        
        // Check the draw
        if (!valid_draw(draws, N)) {
            nb_invalid++;
            if (DISCARD_INVALID) continue;
        } else if (perfect_circle(draws, N)) {
            nb_perfect++;
        }
        nb_sims++;
    }

    free(names);
    free(draws);

    // Print results
    int nb_not_perfect = nb_sims - nb_perfect;
    if (!DISCARD_INVALID) {
        nb_not_perfect -= nb_invalid;
    }
    double pct_invalid = nb_invalid * 100.0 / nb_sims;
    double pct_perfect = nb_perfect * 100.0 / nb_sims;
    double pct_not_perfect = nb_not_perfect * 100.0 / nb_sims;
    pthread_mutex_lock(&write_mutex);
    printf("Ran %d draws of %zu names: %d (%.2f%%) invalid, %d (%.2f%%) perfect, %d (%.2f%%) not perfect\n",
           nb_sims, N, nb_invalid, pct_invalid, nb_perfect, pct_perfect, nb_not_perfect, pct_not_perfect);

    // Save results to file
    fprintf(fptr, "%d,%zu,%d,%d\n", nb_sims, N, nb_invalid, nb_perfect);
    pthread_mutex_unlock(&write_mutex);
}

void* thread_sim(void *start) {
    for (size_t i = (size_t) start; i <= MAX_N; i += NB_THREADS) {
        simulate(i);
    }
}

int main(void) {
    srand((unsigned)time(NULL));

    // CSV file to write results to
    pthread_mutex_lock(&write_mutex);
    fptr = fopen("results.csv", "w");
    fprintf(fptr, "nb_sims,N,nb_invalid,nb_perfect\n");
    pthread_mutex_unlock(&write_mutex);

    // Start simulation threads
    pthread_t threads[NB_THREADS];
    for (size_t i = 0; i < NB_THREADS; i++) {
        pthread_create(&threads[i], NULL, thread_sim, (void *) i+2);
    }

    // Wait for threads to finish
    for (size_t i = 0; i < NB_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    // Close CSV file
    pthread_mutex_lock(&write_mutex);
    fclose(fptr);
    pthread_mutex_unlock(&write_mutex);
}
```
{: file='main.c'}
With the `DISCARD_INVALID` parameter, we can control whether to include invalid draws in the simulated draws. When `DISCARD_INVALID = false`, the total number of possible draws equals the total number of possible permutations of the `names` array (which is equal to $n!$). When `DISCARD_INVALID = true`, the total number of possible draws equals the total number of possible permutations of the `names` array that represent a valid draw, which equals, as we learned earlier, the total number of derangements of the `names` array ($!n$).

## Findings

Let's finally plot the results. I ran 10 million simulations for $n$ going from 2 to 100, twice, once allowing invalid draws and once discarding them. The plots show the simulation results as a solid line and the calculated results as a dashed line.

<iframe width="750" height="420" src="/assets/img/posts/2025-12-26-the_derangement_of_secret_santa/plot_allow_invalid.html"></iframe>

As you can see, the probability of a perfect draw decreases as $n$ increases. Initially, I was surprised that the probability of an invalid draw was constant for larger $n$. But when you look at the expression for this probability and the expression for the subfactorial, it makes a lot of sense because this probability can be approximated by $\frac1e$:

$$
P_{\mathrm{invalid \ draw}} = 1 - P_{\mathrm{valid \ draw}} = 1 - \frac{!n}{n!} = 1 - \frac1{n!} \left[ \frac{n!}{e} \right] \approx 1 - \frac1e = 0.6321205588
$$

<iframe width="750" height="420" src="/assets/img/posts/2025-12-26-the_derangement_of_secret_santa/plot_discard_invalid.html"></iframe>

In a realistic scenario, you do not allow someone to draw themselves, so it makes more sense to look at the results when such invalid draws are not permitted. Here, we can see that for groups of two or three people, the draw is always perfect. This makes sense because you cannot form multiple distinct circles with fewer than four people. However, after that, the probability rapidly decreases, and for a group of six or more people, the probability of a perfect draw becomes less than 50%.

## Compute the Odds Yourself!

Using what we've discovered so far, I've written a small tool that allows you to calculate the probability of a perfect draw, assuming only valid draws are allowed, for any party size $n$. This tool essentially evaluates the following expression:

$$
P_{\mathrm{perfect \ draw \vert valid \ draw}} = \frac{(n-1)!}{!n} = \frac{(n-1)!}{\left\lfloor \frac{n!}{e} + \frac12 \right\rfloor}
$$

> How many people are in your party?
> 
> <div style="text-align: center; margin-bottom: 1rem;"><input min="2" step="1" type="number" value="4" name="nb-people" id="nb-people" onchange="compute_prob()" style="max-width: 6rem;"></div>
> 
> <div id="info-text">Your party has <strong id="nb-valid">0</strong> possible valid draws of which <strong id="nb-perfect">0</strong> are perfect draws, corresponding to a probability of <strong id="procent-perfect">0%</strong> for a perfect draw!</div><div id="too-large-text" hidden>Your party is simply too large to calculate the number of possible draws! Your odds of a perfect draw are close to zero.</div>
{: .prompt-tip }

<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjs/14.8.1/math.min.js" integrity="sha512-ix7qh7Gu4nTiTEktF0EWQAsn0cGwuiDJwuxdX4GGpivcx+PxYdJ/j0nlWyUTONg2bOQV98vk+x+Ee6zYpB5wyA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script>
const nb_digits = 5;
function compute_prob() {
    const nb_people = document.getElementById("nb-people").value;
    const nb_valid_element = document.getElementById("nb-valid");
    const nb_perfect_element = document.getElementById("nb-perfect");
    const prcnt_perfect_element = document.getElementById("procent-perfect");
    const info_text_element = document.getElementById("info-text");
    const too_large_text_element = document.getElementById("too-large-text");

    let nb_perfect = math.factorial(nb_people-1);
    let nb_valid = Math.floor(math.factorial(nb_people) / math.e + 0.5);
    let procent = nb_perfect / nb_valid * 100;

    if (isNaN(procent)) {
        info_text_element.hidden = true;
        too_large_text_element.hidden = false;
        return;
    } else {
        info_text_element.hidden = false;
        too_large_text_element.hidden = true;
    }

    if (nb_valid >= 1e6) {
        nb_valid_element.innerText = nb_valid.toExponential(nb_digits);
    } else {
        nb_valid_element.innerText = nb_valid;
    }
    if (nb_perfect >= 1e6) {
        nb_perfect_element.innerText = nb_perfect.toExponential(nb_digits);
    } else {
        nb_perfect_element.innerText = nb_perfect;
    }
    prcnt_perfect_element.innerText = procent.toFixed(nb_digits) + '%';
}
compute_prob();
</script>

