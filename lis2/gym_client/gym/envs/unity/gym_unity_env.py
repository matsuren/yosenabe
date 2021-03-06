# -*- coding: utf-8 -*-

import websocket
import msgpack
import gym
import io
from PIL import Image
from PIL import ImageOps
from gym import spaces
import numpy as np
import time


class GymUnityEnv(gym.Env):

    def __init__(self):
        websocket.enableTrace(True)
    	self.ws = websocket.create_connection("ws://localhost:4649/CommunicationGym")
        self.action_space = spaces.Discrete(3)
        # self.depth_image_dim = 224 * 224
        self.depth_image_count = 1
        self.observation, _, _, _ = self.receive()


    def reset(self):
        return self.observation



    def step(self, action, id=[0, 0]):

        msg = {}
        msg["command"] = str(action)
        for i in range(len(id)):
            msg["id"+str(i)] = id[i]

        #actiondata = msgpack.packb({"command": str(action),
                                   # "obj_id": id })
        actiondata = msgpack.packb(msg)
        self.ws.send(actiondata)

        # Unity Process

        observation, reward, end_episode, info = self.receive()

        return observation, reward, end_episode, info

    def receive(self):

        while True:

            statedata = self.ws.recv()

            if not statedata:
                continue

            state = msgpack.unpackb(statedata)

            image = []
            for i in xrange(self.depth_image_count):
                image.append(Image.open(io.BytesIO(bytearray(state['image'][i]))))
            depth = []
            for i in xrange(self.depth_image_count):
                d = (Image.open(io.BytesIO(bytearray(state['depth'][i]))))
                depth.append(d)

            # game object info.
            # obj_pos[0]:x, obj_pos[1]:y, obj_pos[2]:z
            obj_cnt = state['obj_cnt']
            #print(obj_cnt)
            obj_pos = np.empty([obj_cnt, 3], dtype=np.float32)
            obj_angle = np.empty([obj_cnt, 3], dtype=np.float32)
            obj_id = np.empty([obj_cnt], dtype=np.int32)
            for i in xrange(obj_cnt):
                obj_pos[i] = np.array( state['obj_pos'][i], dtype=np.float32).reshape(3) 
                obj_angle[i] = np.array( state['obj_angle'][i], dtype=np.float32).reshape(3)
                obj_id[i] = np.array( state['obj_id'][i], dtype=np.int32).reshape(1)

            agent_pos = np.array( state['agent_pos'], dtype=np.float32).reshape(3)
            agent_angle = np.array( state['agent_angle'], dtype=np.float32).reshape(3)
            
            #print agent_pos
            #print obj_pos        
            #print obj_id
            

            observation = {"image": image, "depth": depth}
            reward = state['reward']
            end_episode = state['endEpisode']

            obj_info = {"cnt":obj_cnt, "pos":obj_pos, "angle":obj_angle, "id":obj_id}
            agent_info = {"pos":agent_pos, "angle":agent_angle}

            return observation, reward, end_episode, {"obj_info":obj_info, "agent_info":agent_info}
            break

    def close(self):
        self.ws.close()
