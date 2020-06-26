#! /usr/bin/env python
"""
An implementation of Deep Q-network (DQN) for solo_escape_task
DQN is a Model free, off policy, reinforcement learning algorithm (https://deepmind.com/research/dqn/)
Author: LinZHanK (linzhank@gmail.com)
"""
from __future__ import absolute_import, division, print_function

import sys
import os
import numpy as np
from numpy import random
from numpy import pi
import time
from datetime import datetime
import matplotlib.pyplot as plt
import rospy

from envs.double_escape_discrete_env import DoubleEscapeDiscreteEnv
from agents.dqn import DQNAgent


if __name__ == "__main__":
    env=DoubleEscapeDiscreteEnv()
    agent = DQNAgent(env=env, name='cent_dqn_full', dim_state=env.observation_space[0],
                     num_actions=env.action_space[0]**2, layer_sizes=[256,256], learning_rate=1e-4, warmup_episodes=500)
    date_time = datetime.now().strftime("%Y-%m-%d-%H-%M")
    num_episodes = 30000
    num_steps = env.max_steps
    train_every = 100 # sample k times to train q-net
    episodic_returns, sedimentary_returns = [], []
    episode_counter = 0
    step_counter = 0
    freeze_signal = False
    success_counter = 0
    start_time = time.time()
    while episode_counter<num_episodes:
        # reset env and get state from it
        obs, rewards, done = env.reset(), [], False
        if 'blown' in env.status:
            continue
        agent.linear_epsilon_decay(episode=episode_counter, decay_period=2000)
        for st in range(num_steps):
            # take actions, no action will take if deactivated
            act = agent.epsilon_greedy(obs)
            act0 = int(act/env.action_space[0])
            act1 = act%env.action_space[0]
            action = np.array([act0, act1])
            # step env
            next_obs, rew, done, info = env.step(action)
            # store transitions and train
            if 'blown' in info:
                break
            agent.replay_memory.store([obs.copy(), act, rew, done, next_obs])
            obs = next_obs.copy()
            step_counter += 1
            rewards.append(rew)
            # train agent
            if episode_counter >= agent.warmup_episodes and (not step_counter%train_every):
                for _ in range(train_every):
                    agent.train()
            # log step
            if info.count('escaped')==2:
                success_counter += 1
            rospy.logdebug("\n-\nepisode: {}, step: {}, epsilon: {} \nstate: {} \naction: {} \nnext_state: {} \nreward: {} \ndone: {} \ninfo: {} \nsucceed: {}\n-\n".format(episode_counter+1, st+1, agent.epsilon, obs, act, next_obs, rew, done, info, success_counter))
            if done:
                episode_counter += 1
                # summarize episode
                episodic_returns.append(sum(rewards))
                sedimentary_returns.append(sum(episodic_returns)/(episode_counter))
                rospy.loginfo("\n================================================================\nEpisode: {} \nSteps: {} \nEpsilon: {} \nEpisodicReturn: {} \nAveragedReturn: {} \nEndState: {} \nTotalSuccess: {} \nTimeElapsed: {} \n================================================================n".format(episode_counter, st+1, agent.epsilon, episodic_returns[-1], sedimentary_returns[-1], info, success_counter, time.time()-start_time))
                break

    # save model
    agent.save_model()
    agent.save_params()
    # save returns
    np.save(os.path.join(agent.model_dir, 'ep_returns.npy'), episodic_returns)
    # plot averaged returns
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.suptitle('Averaged Returns')
    ax.plot(sedimentary_returns)
    plt.show()
