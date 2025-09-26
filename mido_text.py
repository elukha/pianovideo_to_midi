import mido

# 新しいMIDIファイルオブジェクトを作成
mid = mido.MidiFile()

# トラックを追加
track = mido.MidiTrack()
mid.tracks.append(track)

# テンポ設定 (メタメッセージ)
# midoはマイクロ秒/四分音符で指定 (120 BPM = 500000)
track.append(mido.MetaMessage('set_tempo', tempo=500000))

# Cメジャースケール
scale = [60, 62, 64, 65, 67, 69, 71, 72]
velocity = 64 # 音量 (0-127)
duration_ticks = 480 # 音の長さ (ティック単位, デフォルトは480 = 四分音符)

for pitch in scale:
    # ノートオン (note_on) メッセージ
    # (channel=0, note=ピッチ, velocity=音量, time=前のイベントからの経過時間)
    # 最初のノートは time=0
    track.append(mido.Message('note_on', channel=0, note=pitch, velocity=velocity, time=0))
    
    # ノートオフ (note_off) メッセージ
    # (time=duration_ticks で指定した時間だけ後に鳴り止む)
    track.append(mido.Message('note_off', channel=0, note=pitch, velocity=0, time=duration_ticks))

# MIDIファイルとして保存
mid.save('c_major_scale_mido.mid')

print("c_major_scale_mido.mid を作成しました。")