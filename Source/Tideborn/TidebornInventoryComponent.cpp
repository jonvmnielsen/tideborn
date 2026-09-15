#include "TidebornInventoryComponent.h"

UTidebornInventoryComponent::UTidebornInventoryComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	Slots.SetNum(MaxSlots);
}

void UTidebornInventoryComponent::BeginPlay()
{
	Super::BeginPlay();
	if (Slots.Num() != MaxSlots)
	{
		Slots.SetNum(MaxSlots);
	}
}

bool UTidebornInventoryComponent::AddItem(FName ItemId, int32 Count)
{
	if (ItemId.IsNone() || Count <= 0)
	{
		return false;
	}

	for (FTidebornItemStack& Slot : Slots)
	{
		if (Slot.ItemId == ItemId)
		{
			Slot.Count += Count;
			return true;
		}
	}

	for (FTidebornItemStack& Slot : Slots)
	{
		if (Slot.IsEmpty())
		{
			Slot.ItemId = ItemId;
			Slot.Count = Count;
			return true;
		}
	}

	return false;
}

bool UTidebornInventoryComponent::RemoveItem(FName ItemId, int32 Count)
{
	if (ItemId.IsNone() || Count <= 0 || CountItem(ItemId) < Count)
	{
		return false;
	}

	int32 Remaining = Count;
	for (FTidebornItemStack& Slot : Slots)
	{
		if (Slot.ItemId != ItemId)
		{
			continue;
		}

		const int32 Take = FMath::Min(Slot.Count, Remaining);
		Slot.Count -= Take;
		Remaining -= Take;
		if (Slot.Count <= 0)
		{
			Slot.ItemId = NAME_None;
			Slot.Count = 0;
		}
		if (Remaining <= 0)
		{
			return true;
		}
	}

	return Remaining <= 0;
}

int32 UTidebornInventoryComponent::CountItem(FName ItemId) const
{
	int32 Total = 0;
	for (const FTidebornItemStack& Slot : Slots)
	{
		if (Slot.ItemId == ItemId)
		{
			Total += Slot.Count;
		}
	}
	return Total;
}

bool UTidebornInventoryComponent::HasItems(const TArray<FTidebornItemStack>& Costs) const
{
	for (const FTidebornItemStack& Cost : Costs)
	{
		if (CountItem(Cost.ItemId) < Cost.Count)
		{
			return false;
		}
	}
	return true;
}

void UTidebornInventoryComponent::PrintInventory() const
{
	FString Line = TEXT("Tideborn Inventory:");
	bool bAny = false;
	for (const FTidebornItemStack& Slot : Slots)
	{
		if (!Slot.IsEmpty())
		{
			bAny = true;
			Line += FString::Printf(TEXT(" %s x%d;"), *Slot.ItemId.ToString(), Slot.Count);
		}
	}
	if (!bAny)
	{
		Line += TEXT(" (empty)");
	}
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 4.f, FColor::Cyan, Line);
	}
	UE_LOG(LogTemp, Log, TEXT("%s"), *Line);
}

void UTidebornInventoryComponent::SetSlots(const TArray<FTidebornItemStack>& InSlots)
{
	Slots = InSlots;
	Slots.SetNum(MaxSlots);
}
