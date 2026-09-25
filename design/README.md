# 圣合丰 品牌应用设计

基于新版木脚 logo 做的第一批应用物料。总览见 `design-board.png`。

## 文件

| 物料 | 给印刷厂 | 预览 / Canva 用 |
|---|---|---|
| 名片正面 | `business-card-front-print-bleed.pdf` | `business-card-front.png` |
| 名片背面（示例文字） | `business-card-back-print-bleed.pdf` | `business-card-back.png` |
| 名片背面（空白，自己加字） | `business-card-back-blank-print-bleed.pdf` | `business-card-back-blank.png` |
| 纸箱唛头标签 | `carton-label-100x150.pdf` | `carton-label-100x150.png` |
| 横版 logo 全彩 | | `logo-horizontal-colour.svg / .png` |
| 横版 logo 纯黑 | | `logo-horizontal-black.svg / .png` |
| 横版 logo 反白 | | `logo-horizontal-white.svg / .png` |

## 名片

- 成品尺寸 **90×54mm**，国内标准名片。
- 印刷 PDF 已含四边各 **3mm 出血**，页面是 96×60mm，直接发给印刷厂即可。
- 正面：品牌棕底 + 米白 logo，底纹是很淡的木纹横线。建议 **300g 以上特种纸**，米白或牛皮纹理纸效果最好。
- 背面：暖白底 + 全彩木脚标志。**背面上的姓名、电话、邮箱、网址、地址都是占位文字**，要换成真实信息。

### 背面在 Canva 里加信息

1. Canva 新建「名片」，尺寸改成 90×54mm
2. 上传 `business-card-back-blank.png` 铺满整张
3. 在竖线右侧加文字，参考 `business-card-back.png` 的位置：
   - 姓名：粗体，约 12pt，颜色 `#3F1A08`
   - 职位：约 6pt，颜色 `#9C6733`
   - 电话 / 邮箱 / 网址 / 地址：约 6.5pt，颜色 `#2A2A2A`；前面的 T / E / W / A 用 `#AE7A44` 粗体
4. 正面直接上传 `business-card-front.png` 铺满

## 纸箱唛头标签

- 尺寸 **100×150mm**，就是最常见的热敏 / 不干胶物流标签尺寸，标签机可以直接打。
- **纯黑单色**，也可以拿去做纸箱印刷版或者刻印章。
- 品名已预填「沙发木脚 SOFA WOODEN LEGS」。型号、木种、尺寸、颜色、数量、毛重、净重、箱号留空，手写或盖章填写。
- 底部是国际通用的 **向上** 和 **怕湿** 包装标志，外贸出口箱通用。

## 横版 logo

木脚在左，圣合丰在右。竖版放不下的地方用它：邮件签名、网站页头、信纸抬头、发票、合同、展会横幅。

## 修改

改 `build_designs.py` 里的颜色、文字或位置后重跑：

```bash
python3 build_designs.py
```

它会调用 `../logo/build_logo.py`，logo 改了这里会自动跟着变。
