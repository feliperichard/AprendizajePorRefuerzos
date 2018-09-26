# Inspired by https://keon.io/deep-q-learning/

import random
import gym
import math
import numpy as np
from collections import deque
from keras.models import clone_model
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam


class DQNCartPoleSolver:
    def __init__(self, n_episodes=1000, max_env_steps=None, gamma=1.0, epsilon=1.0, epsilon_min=0.01,
                 epsilon_log_decay=0.005, alpha=0.01, alpha_decay=0.01, batch_size=32, c=10, monitor=False):
        self.memory = deque(maxlen=100000)
        self.env = gym.make('CartPole-v0')
        if monitor: self.env = gym.wrappers.Monitor(self.env, '../data/cartpole-1', force=True)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_log_decay
        self.alpha = alpha
        self.alpha_decay = alpha_decay
        self.n_episodes = n_episodes
        self.batch_size = batch_size
        self.c = c
        if max_env_steps is not None: self.env._max_episode_steps = max_env_steps

        # Init model
        self.model = Sequential()
        self.model.add(Dense(24, input_dim=4, activation='relu'))
        self.model.add(Dense(48, activation='relu'))
        self.model.add(Dense(2, activation='linear'))
        self.model.compile(loss='mse', optimizer=Adam(lr=self.alpha, decay=self.alpha_decay))

        self.model2 = clone_model(self.model)
        self.model2.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def choose_action(self, state, epsilon):
        return self.env.action_space.sample() if (np.random.random() <= epsilon) else np.argmax(
            self.model.predict(state))

    def get_epsilon(self, t):
        return max(self.epsilon_min, self.epsilon * math.exp(-self.epsilon_decay * t))

    @staticmethod
    def preprocess_state(state):
        return np.reshape(state, [1, 4])

    def replay(self, batch_size):
        x_batch, y_batch = [], []
        minibatch = random.sample(
            self.memory, min(len(self.memory), batch_size))
        for state, action, reward, next_state, done in minibatch:
            # y_target = self.model.predict(state)
            y_target = self.model.predict(state)
            target = reward if done else (reward + self.gamma * np.max(self.model2.predict(next_state)[0]))

            y_target[0][action] = target
            x_batch.append(state[0])
            y_batch.append(y_target[0])

        self.model.fit(np.array(x_batch), np.array(y_batch), batch_size=len(x_batch), verbose=0)

    def run(self):
        scores100 = deque(maxlen=100)
        scores = []
        j = 0  # used for model2 update
        for e in range(self.n_episodes):
            state = self.preprocess_state(self.env.reset())
            done = False
            i = 0
            while not done:
                action = self.choose_action(state, self.get_epsilon(e))
                next_state, reward, done, _ = self.env.step(action)
                next_state = self.preprocess_state(next_state)
                self.remember(state, action, reward, next_state, done)

                self.replay(self.batch_size)

                state = next_state
                i += 1
                j += 1

                # update second model
                if j % self.c == 0:
                    self.model2.set_weights(self.model.get_weights())

            scores100.append(i)
            scores.append(i)

            mean_score = np.mean(scores100)
            if e % 100 == 0:
                print('[Episode {}] - Mean survival time over last 100 episodes was {} ticks.'.format(e, mean_score))

        print('[Episode {}] - Mean survival time over last 100 episodes was {} ticks.'.format(e, mean_score))
        return scores


if __name__ == '__main__':
    agent = DQNCartPoleSolver()
    agent.run()