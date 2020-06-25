#listgen
# import numpy as np
import random
from decimal import *
import pickle
from glob import glob
import os


def range_shuffle(ranges):
    random.shuffle(ranges)
    return ranges

#Balloon Randomization function.  Returns a list of dictionaries that determine
#the order of the bags and the number of balloons per bag.
def balloon_probability_orders(total_number_of_balloons,balloon_setup,randomize):
    num_ranges = len(balloon_setup)
    b_sets = range_shuffle(balloon_setup)
    balloons_per_dist=[]
    if randomize==True:
        while sum(balloons_per_dist) is not total_number_of_balloons or len(balloons_per_dist) is not num_ranges:
            if len(balloons_per_dist) > num_ranges:
                balloons_per_dist= []
            balloons_per_dist.append(random.randint(5,13))
        for i in range(0,num_ranges):
            b_sets[i]['number_of_balloons']=balloons_per_dist[i]
    else:

        for i in range(0,num_ranges):
            b_sets[i]['number_of_balloons']=total_number_of_balloons/num_ranges
    return b_sets
#function that returns a single reward for a single pump
def reward_calc(set_low,set_high):
    cash_money=round((random.uniform(set_low, set_high)),2)
    return cash_money
#Generates the bags of balloons and the balloons themselves
def add_air(total_number_of_balloons,num_ranges,balloon_setup,randomize,reward_low,reward_high,
            subject_directory,practice=False,shuffle_bags=True):
    #calling the balloon randomize function, setting it to x.  Returns a list of dictionaries
    x = balloon_probability_orders(total_number_of_balloons,balloon_setup,randomize)
    #g_code is a list of bags.  Each bag contains balloons of the same pop range
    g_code=[] #g_code: it really is that cool
    bag_ID=0 #counter used to identify what bag a balloon is in
    balloon_counter = 0     #A counter used to mark the balloon's number out of the total number of balloons
    # colors = ['red','blue','green','purple']   #colors for the different balloon types
    # colors = [[141,211,199,1.],[255,255,179,1.],[190,186,218,1.],[251,128,114,1.],
    #           [128,177,211,1.],[253,180,98,1.],[179,222,105,1.],[252,205,229,1.]]
    colors = [[0.6509803921568628, 0.807843137254902, 0.8901960784313725, 1.0],
              [0.12156862745098039, 0.47058823529411764, 0.7058823529411765, 1.0],
              [0.6980392156862745, 0.8745098039215686, 0.5411764705882353, 1.0],
              [0.2, 0.6274509803921569, 0.17254901960784313, 1.0],
              [0.984313725490196, 0.6039215686274509, 0.6, 1.0],
              [0.8901960784313725, 0.10196078431372549, 0.10980392156862745, 1.0],
              [0.9921568627450981, 0.7490196078431373, 0.43529411764705883, 1.0],
              [1.0, 0.4980392156862745, 0.0, 1.0],
              [0.792156862745098, 0.6980392156862745, 0.8392156862745098, 1.0],
              [0.41568627450980394, 0.23921568627450981, 0.6039215686274509, 1.0],
              [1.0, 1.0, 0.6, 1.0],
              [0.6941176470588235, 0.34901960784313724, 0.1568627450980392, 1.0]]
    random.shuffle(colors)
    if practice == True:
        colors = [[0.8509803921568627, 0.8509803921568627, 0.8509803921568627, 1.0],
                  [0.8509803921568627, 0.8509803921568627, 0.8509803921568627, 1.0],
                  [0.8509803921568627, 0.8509803921568627, 0.8509803921568627, 1.0]]
    for balloon_set in x:
        limits=balloon_set['range']
        number_of_balloons=balloon_set['number_of_balloons']
        color = colors[x.index(balloon_set)]
        bag=[]
        for i in range(0,int(number_of_balloons)):
            g_set={'pop':[],'rewards':[],'max_pumps':[],'pump_range':limits,
                   'balloon_in_bag':i,'balloon_number':balloon_counter,
                   'bag_ID_number':bag_ID, 'color':color,
                   'number_of_balloons_in_bag':number_of_balloons}
            balloon_counter+=1
            xx=random.randint(limits[0],limits[1])
            f = [1]*xx
            g_set['max_pumps']=len(f)
            f.append(0)
            pump_rewards=[]
            # reward_dist_type=[]
            for pump in range(60):              #Loop that determines which uniform reward distribtuion to use
            #     reward_dist=random.randint(1,100)    #There is a 10% chance the reward is from the higher distribtuion, 90% lower dist
            #     if reward_dist>7.5:
            #         set_low=H_reward_low
            #         set_high=H_reward_high
            #         reward_dist_type.append('high')
            #     else:
            #         set_low=L_reward_low
            #         set_high=L_reward_high
            #         reward_dist_type.append('low')
            #         f.insert(pump,1)
                money=reward_calc(reward_low,reward_high) #Calling the reward_calc function, setting it to money
                pump_rewards.append(money)   #append reward to list of rewards
            g_set['pop']=f
            g_set['rewards']=pump_rewards    #add list of rewards to ballon dictionary
            #g_set['reward_dist']=reward_dist_type  #add list of reward dist type to balloon dictionary
            bag.append(g_set)    #add the balloon to the bag
        g_code.append(bag)    #add the bag to the g_code
        bag_ID +=1    #increase bag ID number by one
    all_balloons = []
    for bgx in g_code:
        for bx in bgx:
            all_balloons.append(bx)
    g_code = all_balloons
    if practice == False and shuffle_bags == True:
        random.shuffle(g_code)
    else:
        pass
    if practice == True:
        pass
    else:
        try:
            pickles = glob(subject_directory+'/obart_pickles')
            session_num = str(len(pickles))
            pickle.dump(g_code,open(subject_directory+'/obart_pickles/bags_session_'+session_num+'.p','wb'))
        except:
            os.makedirs(subject_directory+'/obart_pickles')
            pickle.dump(g_code,open(subject_directory+'/obart_pickles/bags_session_0.p','wb'))
    return g_code
