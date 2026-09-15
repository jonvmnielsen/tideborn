#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornTypes.h"
#include "TidebornInventoryComponent.generated.h"

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornInventoryComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornInventoryComponent();

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Inventory")
	int32 MaxSlots = 24;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Inventory")
	TArray<FTidebornItemStack> Slots;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Inventory")
	bool AddItem(FName ItemId, int32 Count);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Inventory")
	bool RemoveItem(FName ItemId, int32 Count);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Inventory")
	int32 CountItem(FName ItemId) const;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Inventory")
	bool HasItems(const TArray<FTidebornItemStack>& Costs) const;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Inventory")
	void PrintInventory() const;

	void SetSlots(const TArray<FTidebornItemStack>& InSlots);
};
