# Lyric Sync Calibrator · 字幕校准器

一个**单文件、零依赖、完全离线**的歌词时间轴校准工具。像 YouTube 的同步歌词那样逐字点亮，
但**你可以直接改时间**：点按钮或用键盘微调每句的起止，立刻看到结果，最后导出时间表交给渲染脚本。

> 为什么需要它：给 AI 生成的歌曲做字幕时，"哪一句在几秒"极难对齐 ——
> 音频里唱的乐句与歌词的分行**往往不是一一对应**的，机器只能量出"人声在哪里停"，
> 无法判断"那一停对应第几行"。所以最好的分工是：**人耳定句界 + 机器给精确值 + 工具让调整即时可见**。

## 功能

| 功能 | 说明 |
|---|---|
| 逐字卡拉OK | 已唱完=骨白／正在唱=信号橙＋下划线／未唱=暗影 |
| 拖动进度条 | 任意跳转；点击列表任一行直接定位 |
| 微调（按钮） | 「起」「止」各 4 个按钮（−0.5 / −0.1 / +0.1 / +0.5），也可直接输入秒数 |
| 微调（键盘） | `空格` 播放 ｜ `a`/`d` 起点 ∓ ｜ `w`/`s` 终点 ∓ ｜ `Shift` 加大 5× |
| 连带顺延 | 改一句，下一句自动跟着走，不会"改一条坏一条" |
| 循环本句 | 按 `L` 反复听同一句（校时间最有用） |
| 变速 | 0.5× / 0.75× / 1× / 1.25× |
| 撤销 / 重做 | 随时反悔；还能"恢复本句原值""全部恢复" |
| 改动清单 | 每次操作都在页面显示"第 N 句 止：00:12.34 → 00:12.24" |
| 导出 | 一键导出 `mm:ss.xx → mm:ss.xx  文字` 的文本，或复制到剪贴板 |

## 使用

1. 打开 `index.html`（双击即可，无需服务器、无需联网）
2. 页面里的音频路径默认是 `audio.mp3` —— 把你的音频放到同目录并改名，或点顶栏
   **「📂 选择音频文件」** 手动指定
3. 校对：拖动进度条到有问题的地方 → 点列表里那一行 → `L` 循环 → 用「起」「止」按钮调到顺耳
4. 点 **「⬇ 导出时间表」** 得到时间表文本（格式 `mm:ss.xx → mm:ss.xx  文字`）

> 如果顶栏显示橙色的 **JS 错误** 或 **音频加载失败** 提示，按提示处理（页面不会静默失败）。

## 生成自己的校准器

时间表 JSON 结构：

```json
{
  "duration": 221.93,
  "lines": [
    { "text": "第一句", "start": 6.94, "end": 9.04,
      "chars": [ {"c":"第","start":6.94,"end":7.64}, {"c":"一","start":7.64,"end":8.34} ] }
  ]
}
```

生成（可选：把音频路径写进 HTML）：

```bash
python tools/make_calibrator.py --timing sample/demo_timing.json --audio audio.mp3 --out index.html
```

## 键盘速查

| 键 | 作用 |
|---|---|
| `空格` | 播放 / 暂停 |
| `←` `→` | −0.5s / +0.5s |
| `a` `d` | 当前句**起点** −/+ 步长（`Shift` = 5×） |
| `w` `s` | 当前句**终点** −/+ 步长 |
| `,` `.` | 上一句 / 下一句 |
| `L` | 循环本句开关 |

## License

MIT —— 见 `LICENSE`。仓库不含任何第三方音频或歌词，`sample/` 内为占位文本。

---

## English

**Lyric Sync Calibrator** — a single-file, dependency-free, fully offline tool to align lyric timing
to an audio track. It renders karaoke-style per-character highlighting (like YouTube's synced lyrics)
and lets you **edit the timings directly**: nudge each line's start/end with buttons or keys, with
automatic ripple to the next line, undo/redo, per-line looping, playback speed control, and one-click
export of the resulting `mm:ss.xx → mm:ss.xx  text` table.

Open `index.html`, point it at your audio (top-right **📂** button), play, and adjust.
Build your own from a JSON timing file with `python tools/make_calibrator.py`.
