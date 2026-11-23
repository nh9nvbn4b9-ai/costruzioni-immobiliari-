"""Upscale 4x con Real-ESRGAN (architettura RRDBNet riscritta qui, solo pesi caricati)."""
import sys, numpy as np, torch, torch.nn as nn, torch.nn.functional as F, cv2
torch.set_num_threads(4)

class RDB(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1); s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1); s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)
    def forward(s, x):
        x1 = s.l(s.conv1(x)); x2 = s.l(s.conv2(torch.cat((x, x1), 1)))
        x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1))); x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1)))
        return s.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x

class RRDB(nn.Module):
    def __init__(s, nf=64):
        super().__init__(); s.rdb1 = RDB(nf); s.rdb2 = RDB(nf); s.rdb3 = RDB(nf)
    def forward(s, x):
        return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x

class Net(nn.Module):
    def __init__(s, nf=64, nb=23):
        super().__init__()
        s.conv_first = nn.Conv2d(3, nf, 3, 1, 1); s.body = nn.Sequential(*[RRDB(nf) for _ in range(nb)])
        s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)
    def forward(s, x):
        f = s.conv_first(x); f = f + s.conv_body(s.body(f))
        f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode='nearest')))
        f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode='nearest')))
        return s.conv_last(s.l(s.conv_hr(f)))

net = Net()
sd = torch.load('/tmp/claude-0/models/RealESRGAN_x4plus.pth', map_location='cpu', weights_only=True)
net.load_state_dict(sd.get('params_ema', sd.get('params', sd))); net.eval()
img = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
H, W = img.shape[:2]; T, P = 192, 12
out = np.zeros((H * 4, W * 4, 3), np.float32)
with torch.no_grad():
    for y in range(0, H, T):
        for x in range(0, W, T):
            y0, x0 = max(0, y - P), max(0, x - P); y1, x1 = min(H, y + T + P), min(W, x + T + P)
            t = torch.from_numpy(img[y0:y1, x0:x1]).permute(2, 0, 1)[None]
            o = net(t)[0].permute(1, 2, 0).numpy()
            ty, tx = (y - y0) * 4, (x - x0) * 4; hh, ww = min(T, H - y) * 4, min(T, W - x) * 4
            out[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = o[ty:ty + hh, tx:tx + ww]
cv2.imwrite(sys.argv[2], cv2.cvtColor((out.clip(0, 1) * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR))
print('ok', out.shape)
