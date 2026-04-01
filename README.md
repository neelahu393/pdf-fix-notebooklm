# NotebookLM PDF 繁體中文破字修復工具

修復 NotebookLM 產出的 PDF 中繁體中文字型顯示異常問題。

## 下載

前往 [Releases](../../releases) 下載最新版 `fix_notebooklm_pdf.exe`

## 使用方式

**方法一：拖曳**
將破字的 PDF 直接拖曳到 `fix_notebooklm_pdf.exe` 上放開，自動產生 `原檔名_fixed.pdf`。

**方法二：命令列**
```
fix_notebooklm_pdf.exe input.pdf
fix_notebooklm_pdf.exe input.pdf output.pdf
fix_notebooklm_pdf.exe input.pdf output.pdf 300
```

**參數說明**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| input.pdf | 要修復的 PDF | 必填 |
| output.pdf | 輸出檔名 | 原檔名_fixed.pdf |
| dpi | 解析度（200 簡報用 / 300 高清） | 200 |

## 修復原理

將每頁光柵化為圖片再重新打包，完全繞過字型問題。
修復後為圖片型 PDF（不可選字），適合簡報分享用途。
