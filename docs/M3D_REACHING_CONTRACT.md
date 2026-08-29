# M3D Reaching Contract

State is position and velocity (6D); observation appends 3D goal. At 20 Hz: v'=0.90v+0.05a and x'=clip(x+0.05v',[-1,1]). Action is clipped 3D acceleration. Expert is a=clip(8(goal-position)-4velocity,[-4,4]). Success requires position error below .05 and velocity norm below .05. Chunk-BC predicts H=16 actions and deploys k=4 before replanning. Splits are episode-level (400 train/100 validation).
