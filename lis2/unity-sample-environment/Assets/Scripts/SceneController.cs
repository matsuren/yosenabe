﻿using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.Threading;

namespace MLPlayer
{
	public class SceneController : MonoBehaviour
	{
		//singleton
		protected static SceneController instance;

		public static SceneController Instance {
			get {
				if (instance == null) {
					instance = (SceneController)FindObjectOfType (typeof(SceneController));
					if (instance == null) {
						Debug.LogError ("An instance of" + typeof(SceneController) + "is needed in the scene,but there is none.");
					}
				}
				return instance;
			}
		}

		[SerializeField] float cycleTimeStepSize;
		[SerializeField] float episodeTimeLength;
		[Range (0.1f, 10.0f)]
		[SerializeField] float timeScale = 1.0f;

		[SerializeField] public Agent agent;
		public static AIServer server;
		public static bool FinishFlag = false;
		private Vector3 firstLocation;

		[SerializeField] Environment environment;
		private float lastSendTime;
		private float episodeStartTime = 0f;
		public static ManualResetEvent received = new ManualResetEvent (false);

		void Start ()
		{
			server = new AIServer (agent);
			firstLocation = new Vector3 ();
			firstLocation = agent.transform.position;
			StartNewEpisode ();
			lastSendTime = -cycleTimeStepSize;
		}

		public void TimeOver ()
		{
			agent.EndEpisode ();
		}

		public void StartNewEpisode ()
		{
			episodeStartTime = Time.time;
			environment.OnReset ();
			agent.transform.position = firstLocation;
			agent.StartEpisode ();
		}

		public void FixedUpdate ()
		{
			if (FinishFlag == false) {
				Time.timeScale = timeScale;
				if (lastSendTime + cycleTimeStepSize <= Time.time) {
					lastSendTime = Time.time;
	
					if (Time.time - episodeStartTime > episodeTimeLength) {
						TimeOver ();
					}
					if (agent.state.endEpisode) {
						StartNewEpisode ();
					}
					received.Reset ();
					agent.UpdateState ();

					// set positions of all game objects as state
					Object[] objs = environment.getGameObjs();
					int itemCnt = objs.Length;
					Debug.Log (itemCnt);
					int j = 0;
					agent.state.obj_pos = new float[itemCnt][];
					agent.state.obj_id = new int[itemCnt];
					foreach (GameObject obj in objs) {
						agent.state.obj_pos [j] = new float[3];
						agent.state.obj_pos [j] [0] = obj.transform.position.x;
						agent.state.obj_pos [j] [1] = obj.transform.position.y;
						agent.state.obj_pos [j] [2] = obj.transform.position.z;
						agent.state.obj_id [j] = obj.GetInstanceID ();
						j++;
					}
					agent.state.obj_cnt = itemCnt;

					server.PushAgentState (agent.state);
					received.WaitOne ();
					agent.ResetState ();
				}
			} else {
				EditorApplication.isPlaying = false;
			}
		}
	}
}
