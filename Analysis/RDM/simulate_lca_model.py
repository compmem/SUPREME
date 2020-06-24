import numpy as np
from numba import jit


# nu must be greater than 0 with kappa, beta, and pi equal to 0 to use FFI/DDM
# both kappa and beta must be greater than 0 with nu and pi equal to 0 to use LCA
# pi must be greater than 0 with kappa, beta, and nu equal to 0 to use DDM with scaled noise
@jit(nopython=True)
def uber_sim(rho, nu=0.0, kappa=0.0, beta=0.0, alpha=5.0, pi=0.0, dt=0.01,
			 tau=0.1, eta=1.0, max_time=5.0, xinit=0.0, t0=0.0):
	# allocate and initialize variables
	num_choices = len(rho)
	drive = np.zeros(num_choices)
	x = np.zeros(num_choices)
	dt_tau = dt/tau
	sqrt_dt_tau = np.sqrt(dt_tau)
	sqrt_dt_tau_eta = sqrt_dt_tau*eta
	ffi_param = nu/(num_choices-1.0)
	max_iter = int(max_time/dt)

	# reset in prep for the next sim
	crossed_ind = 0
	crossed = 0.0
	x_sum_temp = 0.0
	drive_sum_temp = 0.0
	for i in range(num_choices):
		x[i] = xinit
		drive[i] = rho[i]*dt_tau + np.random.randn()*sqrt_dt_tau_eta
		drive_sum_temp += drive[i]

	# loop over time
	for t in range(1, max_iter+1):
		x_sum = x_sum_temp
		x_sum_temp = 0.0
		drive_sum = drive_sum_temp
		drive_sum_temp = 0.0
		for i in range(num_choices):
			# update accumulators
			x[i] += drive[i] - ffi_param*(drive_sum-drive[i]) - (kappa*x[i] + beta*(x_sum - x[i]))*dt_tau
			if x[i] < 0.0:
				x[i] = 0.0
			x_sum_temp += x[i]

			# calculate drive for next iteration
			drive[i] = rho[i]*dt_tau + np.random.randn()*sqrt_dt_tau_eta + np.random.randn()*sqrt_dt_tau*pi*rho[i]
			drive_sum_temp += drive[i]

			# check to see if either accumulator has crossed
			# note the test for precision errors
			if (x[i]+0.0000001) >= alpha:
				# see if we keep the new accumulator
				if x[i] > crossed:
					# it's higher, so assume it crossed first
					crossed = x[i]
					crossed_ind = i+1
				elif (crossed-x[i]) < 0.0000001:
					# they are close so flip a coin
					if np.random.uniform(0, 1) < .5:
						crossed_ind = i+1
						crossed = x[i]
		if crossed > 0.0:
			# we crossed
			break

	# so free and finish
	return (t*dt)+t0, crossed_ind


@jit(nopython=True)
def uber_multi_sim(rho, nu=0.0, kappa=0.0, beta=0.0, alpha=5.0, pi=0.0, dt=0.01,
                   tau=0.1, eta=1.0, max_time=5.0, xinit=0.0, nsims=50000,
                   t0=0.0):
	# allocate for our return info
	rts = np.empty(nsims)
	choices = np.empty(nsims, dtype=np.int32)
	# loop over sims
	for n in range(nsims):
		# save the rt and choice
		rt, choice = uber_sim(rho, nu, kappa, beta, alpha, pi, dt, tau, eta,
							  max_time, xinit, t0)
		rts[n] = rt
		choices[n] = choice
	# so free and finish
	return rts, choices
