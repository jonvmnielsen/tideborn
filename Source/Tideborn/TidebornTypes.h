#pragma once

#include "CoreMinimal.h"
#include "TidebornTypes.generated.h"

USTRUCT(BlueprintType)
struct FTidebornItemStack
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn")
	FName ItemId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn")
	int32 Count = 0;

	bool IsEmpty() const { return ItemId.IsNone() || Count <= 0; }
};

USTRUCT(BlueprintType)
struct FTidebornRecipe
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn")
	FName RecipeId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn")
	TArray<FTidebornItemStack> Costs;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn")
	FTidebornItemStack Output;
};
