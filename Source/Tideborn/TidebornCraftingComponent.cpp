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
	PrimaryComponentTick.bCanEverTick = true;

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

		{
		FTidebornRecipe R;
		R.RecipeId = FName(TEXT("KelpBait"));
		R.Costs.Add({FName(TEXT("Stick")), 1});
		R.Costs.Add({FName(TEXT("Stone")), 1});
		R.Output = {FName(TEXT("KelpBait")), 1};
		Recipes.Add(R);
	}
	SelectedRecipeIndex = 0;
}

void UTidebornCraftingComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornCraftingComponent::BindHotkeys));
	}
	ShowMenu(12.f);
}

void UTidebornCraftingComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	if (Now > MenuVisibleUntil)
	{
		return;
	}

	MenuRefreshAccum += DeltaTime;
	if (MenuRefreshAccum >= 0.35f)
	{
		MenuRefreshAccum = 0.f;
		RefreshStickyHud();
	}
}

void UTidebornCraftingComponent::ShowMenu(float Seconds)
{
	if (UWorld* World = GetWorld())
	{
		MenuVisibleUntil = World->GetTimeSeconds() + Seconds;
	}
	RefreshStickyHud();
}

void UTidebornCraftingComponent::RefreshStickyHud()
{
	if (!GEngine)
	{
		return;
	}

	UTidebornInventoryComponent* Inv = GetInventory();
	FString InvLine = TEXT("Inv:");
	bool bAny = false;
	if (Inv)
	{
		for (const FTidebornItemStack& Slot : Inv->Slots)
		{
			if (!Slot.IsEmpty())
			{
				bAny = true;
				InvLine += FString::Printf(TEXT(" %sx%d"), *Slot.ItemId.ToString(), Slot.Count);
			}
		}
	}
	if (!bAny)
	{
		InvLine += TEXT(" (empty)");
	}
	GEngine->AddOnScreenDebugMessage(92010, 2.f, FColor::Cyan, InvLine);

	if (!Recipes.IsValidIndex(SelectedRecipeIndex))
	{
		return;
	}

	const FTidebornRecipe& R = Recipes[SelectedRecipeIndex];
	FString Costs;
	for (const FTidebornItemStack& C : R.Costs)
	{
		const int32 Have = Inv ? Inv->CountItem(C.ItemId) : 0;
		Costs += FString::Printf(TEXT(" %s %d/%d"), *C.ItemId.ToString(), Have, C.Count);
	}

	const FString Sel = FString::Printf(
		TEXT("Recipe %d/%d: %s -> %sx%d |%s   (scroll / [ ] cycle, C craft, I refresh)"),
		SelectedRecipeIndex + 1, Recipes.Num(),
		*R.RecipeId.ToString(), *R.Output.ItemId.ToString(), R.Output.Count, *Costs);
	GEngine->AddOnScreenDebugMessage(92011, 2.f, FColor::Yellow, Sel);

	for (int32 i = 0; i < Recipes.Num(); ++i)
	{
		const FTidebornRecipe& Row = Recipes[i];
		const FString Line = FString::Printf(TEXT("%s %d) %s"),
			(i == SelectedRecipeIndex) ? TEXT(">") : TEXT(" "),
			i + 1, *Row.RecipeId.ToString());
		GEngine->AddOnScreenDebugMessage(92020 + i, 2.f, (i == SelectedRecipeIndex) ? FColor::Yellow : FColor::White, Line);
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
	IC->BindKey(EKeys::MouseScrollUp, IE_Pressed, this, &UTidebornCraftingComponent::OnScrollUp);
	IC->BindKey(EKeys::MouseScrollDown, IE_Pressed, this, &UTidebornCraftingComponent::OnScrollDown);
	UE_LOG(LogTemp, Log, TEXT("TidebornCraft: bound C/I/[ ]/scroll"));
}

void UTidebornCraftingComponent::OnCraftKey()
{
	ShowMenu(20.f);
	TryCraftSelected();
}

void UTidebornCraftingComponent::OnInventoryKey()
{
	ShowMenu(25.f);
}

void UTidebornCraftingComponent::OnPrevRecipeKey()
{
	CycleRecipe(-1);
}

void UTidebornCraftingComponent::OnNextRecipeKey()
{
	CycleRecipe(1);
}

void UTidebornCraftingComponent::OnScrollUp()
{
	CycleRecipe(-1);
}

void UTidebornCraftingComponent::OnScrollDown()
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
	ShowMenu(20.f);
}

void UTidebornCraftingComponent::SelectRecipeById(FName RecipeId)
{
	for (int32 i = 0; i < Recipes.Num(); ++i)
	{
		if (Recipes[i].RecipeId == RecipeId)
		{
			SelectedRecipeIndex = i;
			ShowMenu(20.f);
			return;
		}
	}
}

void UTidebornCraftingComponent::PrintSelected() const
{
	const_cast<UTidebornCraftingComponent*>(this)->RefreshStickyHud();
}

void UTidebornCraftingComponent::PrintRecipes() const
{
	const_cast<UTidebornCraftingComponent*>(this)->RefreshStickyHud();
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
			GEngine->AddOnScreenDebugMessage(92012, 10.f, FColor::Orange,
				FString::Printf(TEXT("Need more mats for %s"), *RecipeId.ToString()));
		}
		ShowMenu(20.f);
		return false;
	}

	for (const FTidebornItemStack& Cost : Found->Costs)
	{
		Inv->RemoveItem(Cost.ItemId, Cost.Count);
	}
	Inv->AddItem(Found->Output.ItemId, Found->Output.Count);

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(92012, 10.f, FColor::Green,
			FString::Printf(TEXT("Crafted %s x%d"), *Found->Output.ItemId.ToString(), Found->Output.Count));
	}
	ShowMenu(20.f);
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

