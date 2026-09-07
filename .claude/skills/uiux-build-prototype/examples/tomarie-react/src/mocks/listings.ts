import type { Listing } from "@/components/listing-card";

/* サンプル物件（上流入力なし — pt-spec assumptions 参照） */
export const LISTINGS: Listing[] = [
  { id: "umi", scene: "sea", title: "海が見える古民家 一棟貸し", area: "千葉・館山 ・ 海まで徒歩3分", rating: "4.92", price: "¥18,000" },
  { id: "yama", scene: "cabin", title: "森のサウナ付きキャビン", area: "長野・軽井沢 ・ 薪サウナ", rating: "4.88", price: "¥24,000" },
  { id: "machi", scene: "machiya", title: "商店街の二階、暮らすように泊まる部屋", area: "京都・出町柳 ・ 銭湯すぐ", rating: "4.79", price: "¥9,500" },
  { id: "shima", scene: "port", title: "島の港が見えるゲストハウス個室", area: "広島・尾道 ・ 自転車貸出あり", rating: "4.95", price: "¥7,200" },
];

export const PRIMARY_LISTING = LISTINGS[0];
