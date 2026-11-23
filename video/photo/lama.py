"""Inpainting con LaMa (big-lama TorchScript). Uso: lama.py img.png mask.png out.png"""
import sys, numpy as np, torch, cv2
torch.set_num_threads(4)
m = torch.jit.load('/tmp/claude-0/models/big-lama.pt', map_location='cpu').eval()
img = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB)
mask = cv2.imread(sys.argv[2], 0)
H, W = img.shape[:2]
ph, pw = (8 - H % 8) % 8, (8 - W % 8) % 8
ip = np.pad(img, ((0, ph), (0, pw), (0, 0)), mode='reflect')
mp = np.pad(mask, ((0, ph), (0, pw)), mode='reflect')
x = torch.from_numpy(ip).permute(2, 0, 1)[None].float() / 255
mk = (torch.from_numpy(mp)[None, None].float() / 255 > 0.5).float()
with torch.no_grad():
    out = m(x, mk)
o = (out[0].permute(1, 2, 0).numpy() * 255).clip(0, 255).astype(np.uint8)[:H, :W]
cv2.imwrite(sys.argv[3], cv2.cvtColor(o, cv2.COLOR_RGB2BGR))
print('ok', o.shape)
