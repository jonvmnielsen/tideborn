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
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Craft")
	TArray<FTidebornRecipe> Recipes;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Craft")
	int32 SelectedRecipeIndex = 0;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	bool TryCraft(FName RecipeId);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	bool TryCraftSelected();

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void CycleRecipe(int32 Delta);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void SelectRecipeById(FName RecipeId);

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void PrintRecipes() const;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void PrintSelected() const;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Craft")
	void ShowMenu(float Seconds = 20.f);

private:
	float MenuVisibleUntil = 0.f;
	float MenuRefreshAccum = 0.f;

	UTidebornInventoryComponent* GetInventory() const;
	void BindHotkeys();
	void OnCraftKey();
	void OnInventoryKey();
	void OnPrevRecipeKey();
	void OnNextRecipeKey();
	void OnScrollUp();
	void OnScrollDown();
	void RefreshStickyHud();
};
