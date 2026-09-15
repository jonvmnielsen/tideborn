#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "TidebornTypes.h"
#include "TidebornSaveGame.generated.h"

UCLASS()
class TIDEBORN_API UTidebornSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY(VisibleAnywhere, Category="Tideborn")
	TArray<FTidebornItemStack> InventorySlots;

	UPROPERTY(VisibleAnywhere, Category="Tideborn")
	TArray<FTransform> BuiltPieces;
};
