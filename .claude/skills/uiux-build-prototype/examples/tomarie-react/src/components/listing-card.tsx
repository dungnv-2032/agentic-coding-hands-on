import { Star } from "lucide-react";
import { FavButton } from "./fav-button";
import { Photo, type SceneId } from "./photo";

export interface Listing {
  id: string;
  scene: SceneId;
  title: string;
  area: string;
  rating: string;
  price: string;
}

/* 物件カード — 写真が主役（design.notes）。価格は「¥/泊」併記。♥はローカル状態でトグル */
export function ListingCard({
  listing,
  fav,
  onToggleFav,
  onClick,
}: {
  listing: Listing;
  fav: boolean;
  onToggleFav: () => void;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={onClick ? "cursor-pointer transition-[filter] hover:brightness-[.98] active:scale-[.995]" : undefined}
    >
      <div className="relative">
        <Photo scene={listing.scene} className="aspect-[4/3] rounded-lg" />
        <div className="absolute right-2.5 top-2.5">
          <FavButton on={fav} onToggle={onToggleFav} />
        </div>
      </div>
      <div className="mt-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-bold">{listing.title}</div>
          <div className="text-sm text-muted-foreground">{listing.area}</div>
        </div>
        <span className="flex shrink-0 items-center gap-1 text-sm">
          <Star className="size-3.5 fill-foreground" /> {listing.rating}
        </span>
      </div>
      <div className="mt-0.5 text-sm">
        <b className="tabular">{listing.price}</b>
        <span className="text-muted-foreground"> /泊</span>
      </div>
    </div>
  );
}
