from midiutil import MIDIFile

# MIDIFileオブジェクトを作成 (トラック数 = 1)
MyMIDI = MIDIFile(1)

# 設定
track = 0   # トラック番号
channel = 0 # チャンネル番号
time = 0    # 開始時間 (拍)
duration = 1 # 音の長さ (拍)
tempo = 120  # テンポ (BPM)
volume = 100 # 音量 (0-127)

# テンポを設定
MyMIDI.addTempo(track, time, tempo)

# CメジャースケールのMIDIノート番号
# C4, D4, E4, F4, G4, A4, B4, C5
scale = [60, 62, 64, 65, 67, 69, 71, 72]

# ノートを追加
for i, pitch in enumerate(scale):
    # addNote(トラック, チャンネル, ピッチ, 開始時間, 長さ, 音量)
    print(f"ピッチ pitch = {pitch}")
    print(f"開始時間time + i = {time+i}")
    MyMIDI.addNote(track, channel, pitch, time + i, duration, volume)

# MIDIファイルとして保存
with open("c_major_scale.mid", "wb") as output_file:
    MyMIDI.writeFile(output_file)

print("c_major_scale.mid を作成しました。")