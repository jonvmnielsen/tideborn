#include "TidebornCraftingComponent.h"
#include "TidebornInventoryComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "TimerManager.h"
#include "Engine/World.h"

UTidebornCraftingComponent::UTidebornCraftingComponent()
{
	PrimaryComponentTick.bCanEverTick = false;

	// Foundation first so Camp build loop is the default craft target
	{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("Foundation"));
		R.Costs.Add({FName(TEXT("Wood")), 5});
		R.Output = {FName(TEXT("Foundation")), 1};
		Recipes.Add(R);
	}
	{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("Stick"));
		R.Costs.Add({FName(TEXT("Wood")), 2});
		R.Output = {FName(TEXT("Stick")), 1};
		Recipes.Add(R);
	}
	{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("CampfireKit"));
		R.Costs.Add({FName(TEXT("Stick")), 3});
		R.Costs.Add({FName(TEXT("Stone")), 2});
		R.Output = {FName(TEXT("CampfireKit")), 1};
		Recipes.Add(R);
	}

	SelectedRecipeIndex = 0; // Foundation
}

void UTidebornCraftingComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornCraftingComponent::BindHotkeys));
	}
}

UTidebornInventoryComponent* UTidebornCraftingComponent::GetInventory() const
{
	return GetOwner() ? GetOwner()->FindComponentByClass<UTidebornInventoryComponent>() : nullptr;
}

void UTidebornCraftingComponent::BindHotkeys()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC && GetWorld())
	{
		PC = GetWorld()->GetFirstPlayerController();
	}

	UInputComponent* IC = Pawn ? Pawn->InputComponent : nullptr;
	if (!IC && PC)
	{
		IC = PC->InputComponent;
	}
	if (!IC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornCraftingComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	IC->BindKey(EKeys::C, IE_Pressed, this, &UTidebornCraftingComponent::OnCraftKey);
	IC->BindKey(EKeys::I, IE_Pressed, this, &UTidebornCraftingComponent::OnInventoryKey);
	IC->BindKey(EKeys::LeftBracket, IE_Pressed, this, &UTidebornCraftingComponent::OnPrevRecipeKey);
	IC->BindKey(EKeys::RightBracket, IE_Pressed, this, &UTidebornCraftingComponent::OnNextRecipeKey);
	UE_LOG(LogTemp, Log, TEXT("TidebornCraft: bound C/I/[ /]"));
}

void UTidebornCraftingComponent::OnCraftKey()
{
	TryCraftSelected();
}

void UTidebornCraftingComponent::OnInventoryKey()
{
	if (UTidebornInventoryComponent* Inv = GetInventory())
	{
		Inv->PrintInventory();
	}
	PrintRecipes();
	PrintSelected();
}

void UTidebornCraftingComponent::OnPrevRecipeKey()
{
	CycleRecipe(-1);
}

void UTidebornCraftingComponent::OnNextRecipeKey()
{
	CycleRecipe(1);
}

void UTidebornCraftingComponent::CycleRecipe(int32 Delta)
{
	if (Recipes.Num() <= 0)
	{
		return;
	}
	SelectedRecipeIndex = (SelectedRecipeIndex + Delta) % Recipes.Num();
	if (SelectedRecipeIndex < 0)
	{
		SelectedRecipeIndex += Recipes.Num();
	}
	PrintSelected();
}

void UTidebornCraftingComponent::SelectRecipeById(FName RecipeId)
{
	for (int32 i = 0; i < Recipes.Num(); ++i)
	{
		if (Recipes[i].RecipeId == RecipeId)
		{
			SelectedRecipeIndex = i;
			PrintSelected();
			return;
		}
	}
}

void UTidebornCraftingComponent::PrintSelected() const
{
	if (!Recipes.IsValidIndex(SelectedRecipeIndex))
	{
		return;
	}
	const FTidebornRecipe& R = Recipes[SelectedRecipeIndex];
	FString Costs;
	for (const FTidebornItemStack& C : R.Costs)
	{
		Costs += FString::Printf(TEXT(" %sx%d"), *C.ItemId.ToString(), C.Count);
	}
	const FString Line = FString::Printf(
		TEXT("Craft selected [%d/%d]: %s -> %s x%d | cost:%s  ( [ ] cycle, C craft )"),
		SelectedRecipeIndex + 1, Recipes.Num(),
		*R.RecipeId.ToString(), *R.Output.ItemId.ToString(), R.Output.Count, *Costs);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 4.f, FColor::Yellow, Line);
	}
}

bool UTidebornCraftingComponent::TryCraft(FName RecipeId)
{
	UTidebornInventoryComponent* Inv = GetInventory();
	if (!Inv)
	{
		return false;
	}

	const FTidebornRecipe* Found = Recipes.FindByPredicate([&](const FTidebornRecipe& R) { return R.RecipeId == RecipeId; });
	if (!Found)
	{
		return false;
	}

	if (!Inv->HasItems(Found->Costs))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Orange,
				FString::Printf(TEXT("Need more mats for %s (I shows recipes)"), *RecipeId.ToString()));
		}
		return false;
	}

	for (const FTidebornItemStack& Cost : Found->Costs)
	{
		Inv->RemoveItem(Cost.ItemId, Cost.Count);
	}
	Inv->AddItem(Found->Output.ItemId, Found->Output.Count);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Green,
			FString::Printf(TEXT("Crafted %s x%d"), *Found->Output.ItemId.ToString(), Found->Output.Count));
	}
	return true;
}

bool UTidebornCraftingComponent::TryCraftSelected()
{
	if (!Recipes.IsValidIndex(SelectedRecipeIndex))
	{
		return false;
	}
	return TryCraft(Recipes[SelectedRecipeIndex].RecipeId);
}

void UTidebornCraftingComponent::PrintRecipes() const
{
	for (int32 i = 0; i < Recipes.Num(); ++i)
	{
		const FTidebornRecipe& R = Recipes[i];
		FString Line = FString::Printf(TEXT("%s%d) %s -> %s x%d |"),
			(i == SelectedRecipeIndex) ? TEXT("> ") : TEXT("  "),
			i + 1, *R.RecipeId.ToString(), *R.Output.ItemId.ToString(), R.Output.Count);
		for (const FTidebornItemStack& C : R.Costs)
		{
			Line += FString::Printf(TEXT(" %s x%d"), *C.ItemId.ToString(), C.Count);
		}
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 5.f, (i == SelectedRecipeIndex) ? FColor::Yellow : FColor::White, Line);
		}
	}
}
