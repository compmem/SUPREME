

#ifndef LCA_MT_CU_H
#define LCA_MT_CU_H
#include <stdio.h>
extern "C"
{

// Load helpers from cutools
#include "mt_rand.cu.h"

#define NITEMS %(nitems)d
#define NSIMS %(nsims)d
#define NBINS %(nbins)d
#define MODEL_ID %(model_id)d


struct model_params
{
  // simulation params
  float *out_time;
  float *x_out;
  float *confidence;
  int *x_ind;
  float *x_init;
  float *bins;
  int *bin_ind;
  float sd0;
  float sd_min;
  float r;
  float p;
  int max_iter;
  float max_time;
  float K;
  float L;
  float U;
  float eta;
  float thresh;
  float alpha;
  float dt;
  float tau;
  float dt_tau;
  float sqrt_dt_tau;
  int truncate;
};


// set up the MT RNG
__device__ static MersenneTwisterState mtState[NSIMS];

__global__ void setup_sim()
{
  // get the thread id
  unsigned int idx = __mul24(blockIdx.x, blockDim.x) + threadIdx.x;

  // make sure we're not out of the range
  if (idx >= NSIMS)
  {
    // outside the range of valid lists
    return;
  }

  // initialize the MT RNG
  MersenneTwisterInitialise(mtState[idx], idx);
}

// in-place version, that does not store the accumulator values
__global__
void iaccumulate(model_params *params)
{
  // get the kernel index
  unsigned int idx = __mul24(blockIdx.x, blockDim.x) + threadIdx.x;

  // make sure we're not out of the range
  if (idx >= NSIMS)
  {
    // outside the range of valid lists
    return;
  }

  // some counters
  int t = 0;
  int i,b;

  int crossed = 0;

  // input
  float I[NITEMS];

  // output set to non-response
  params->x_ind[idx] = -1;

  // accumulators
  float x[NITEMS];

  // track crossing val
  float x_cross_val = 0.0;

  // for lateral inhibition
  float lx, sumx_new, sumsqx_new, prodx_new;
  float sumx = 0.0;
  float sumsqx = 0.0;
  float prodx = 0.0;
  float cumprodx = 0.0;

  // for ffi
  float xi[NITEMS];
  float fx, sumxi_new, prodxi_new;
  float sumxi=0;
  float cumsumxi=0.0;
  float prodxi=1.0;
  float cumprodxi=0.0;

  // for variance of xi
  float varxi=0;
  float mean_xi, var_diff;
  float cumsumxi_s=0.0;

  // for spotlight
  float sda_t;

  // calculate starting I
  for (i=0; i<NITEMS; i++)
  {
    // set the I to zero
    x[i] = params->x_init[i];
    sumsqx += (x[i]*x[i]);
    sumx += x[i];
    I[i] = 0.0;
  }

  // get the new standard deviation
  sda_t = (params->sd0 - (params->r)*(cumsumxi_s));
  if (sda_t < params->sd_min)
  {
    sda_t = params->sd_min;
  }

  // loop over bins accumulating input for each choice
  sda_t *= sqrtf(2);
  for (b=0; b<NBINS; b++)
  {
    // get the CDF for that bin
    I[params->bin_ind[b]] += (params->p)*0.5*((1+erff(params->bins[b*2+1]/sda_t)) -
					      (1+erff(params->bins[b*2]/sda_t)));
  }

  // init the x and calc the first input
  prodx = 1.0;
  for (i=0; i<(NITEMS); i++)
  {
    prodx *= x[i];

    // ffi
    xi[i] = ((I[i])*(params->dt_tau)) +
      (params->eta*mt_randn(mtState[idx],idx)*params->sqrt_dt_tau);
    sumxi += xi[i];
    prodxi *= xi[i];
  }

  // reset I and calc varxi
  mean_xi = sumxi/NITEMS;
  varxi = 0.0;
  for (i=0; i<NITEMS; i++)
  {
    // set the I to zero (will be set at top of time loop)
    I[i] = 0.0;

    // add squared diff to var sum
    var_diff = (xi[i]-mean_xi);
    varxi += var_diff * var_diff;
  }
  // get mean of squared diffs
  varxi /= NITEMS;



  // add to the cumsum of the scaled sum xi
  cumsumxi_s += (params->alpha - sumx) * (params->dt/params->tau);
  // loop over time
  for (t=1; t<=params->max_iter; t++)
  {
    // get the sum for the lateral inhibition and ffi
    sumx_new = 0.;
    sumsqx_new = 0.;
    prodx_new = 1.;
    sumxi_new = 0.;
    prodxi_new = 1.;

    sda_t = (params->sd0 - (params->r)*(cumsumxi_s));
    if (sda_t < params->sd_min)
    {
      sda_t = params->sd_min;
    }

    // loop over bins accumulating input for each choice
    sda_t *= sqrtf(2);
    for (b=0; b<NBINS; b++)
    {
      // get the CDF for that bin
      I[params->bin_ind[b]] += (params->p)*0.5*((1+erff(params->bins[b*2+1]/sda_t)) -
      					(1+erff(params->bins[b*2]/sda_t)));
    }

    // loop over items and calc input for FFI
    for (i=0; i<NITEMS; i++)
    {
      // calculate the lateral inhibition
      lx = sumx - x[i];
      fx = (sumxi - xi[i])/(NITEMS-1);  // Note the NITEMS-1 scale

      // determine the change in x
      x[i] += xi[i] - (params->U*fx) -
	(params->K*x[i] + params->L*lx)*(params->dt_tau);

      // make sure not below zero
      if ((x[i] < 0) && (params->truncate))
      {
	x[i] = 0.0;
      }

      // see if crossed thresh
      if (x[i] >= params->thresh)
      {
	// crossed, but we want to make sure to calculate all vals
	if (x[i] > x_cross_val)
	{
	  // then move to this one
	  crossed = 1;
	  params->x_ind[idx] = i;
	  x_cross_val = x[i];
	}
      }

      // determine the next input
      xi[i] = ((I[i])*(params->dt_tau)) +
	(params->eta*mt_randn(mtState[idx],idx)*params->sqrt_dt_tau);
      sumxi_new += xi[i];
      prodxi_new *= xi[i];

      // add the sumx
      sumx_new += x[i];
      sumsqx_new += (x[i]*x[i]);
      prodx_new *= x[i];
    }

    if (crossed == 1)
    {
      break;
    }
    else
    {
      // we're gonna keep going
      sumx = sumx_new;
      sumsqx = sumsqx_new;
      prodx = prodx_new;
      cumprodx += prodx;
      sumxi = sumxi_new;
      prodxi = prodxi_new;
      cumsumxi += sumxi;
      cumprodxi += prodxi;

      // reset I and calc varxi
      mean_xi = sumxi/NITEMS;
      varxi = 0.0;
      for (i=0; i<NITEMS; i++)
      {
	// set the I to zero (will be set at top of time loop)
	I[i] = 0.0;

	// add squared diff to var sum
	var_diff = (xi[i]-mean_xi);
	varxi += var_diff * var_diff;
      }
      // get mean of squared diffs
      varxi /= NITEMS;

      // add to the cumsum of the scaled sum xi
      cumsumxi_s += (params->alpha - sumx) * (params->dt/params->tau);
    }

  }

  // save the confidence
  params->confidence[idx] = x_cross_val/sumx_new;

  // set the out_time
  params->out_time[idx] = t;
  for (i=0; i<NITEMS; i++)
  {
    params->x_out[idx*NITEMS+i] = x[i];
  }
}

}


#endif
