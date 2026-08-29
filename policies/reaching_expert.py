import numpy as np
KP=8.;KD=4.
def action(obs):return np.clip(KP*(obs[6:9]-obs[:3])-KD*obs[3:6],-4,4).astype('f')
