#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornTypes.h"
#include "TidebornCraftingComponent.generated.h"

class UTidebornInventoryComponent;

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornCraftingComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornCraftingComponent();

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Craft")
	TArray<FTidebornRecipe> Recipes;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	bool TryCraft(FName RecipeId);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void TryCraftFirstAffordable();

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void PrintRecipes() const;

private:
	UTidebornInventoryComponent* GetInventory() const;
	void BindHotkeys();
	void OnCraftKey();
	void OnInventoryKey();
};
